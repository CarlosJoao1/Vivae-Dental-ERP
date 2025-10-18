import type { Line } from "@/api/sales";

export function calcGross(ln: Partial<Line> | any): number {
  const q = ln?.qty || 0;
  const p = ln?.price || 0;
  return q * p;
}

export function calcDiscount(ln: Partial<Line> | any, gross?: number): number {
  const g = typeof gross === "number" ? gross : calcGross(ln);
  const dr = Number((ln as any)?.discount_rate || 0);
  const da = Number((ln as any)?.discount_amount || 0);
  if (da) return da;
  if (dr) return g * (dr / 100);
  return 0;
}

export function calcNet(ln: Partial<Line> | any): number {
  const g = calcGross(ln);
  const d = calcDiscount(ln, g);
  return Math.max(0, g - d);
}

export function sumGross(lines: Array<Partial<Line> | any>): number {
  return (lines || []).reduce((s, ln) => s + calcGross(ln), 0);
}

export function sumAfterLine(lines: Array<Partial<Line> | any>): number {
  return (lines || []).reduce((s, ln) => s + calcNet(ln), 0);
}

export function computeGlobalDiscount(hdr: any, afterLine: number): number {
  const rate = Number(hdr?.discount_rate || 0);
  const amount = Number((hdr as any)?.discount_amount || 0);
  if (rate > 0) return afterLine * (rate / 100);
  return amount || 0;
}

export function computeTotals(hdr: any, lines: Array<Partial<Line> | any>) {
  const gross = sumGross(lines);
  const after = sumAfterLine(lines);
  const globalDisc = computeGlobalDiscount(hdr, after);
  const baseTax = Math.max(0, after - (globalDisc || 0));
  const taxRate = Number(hdr?.tax_rate || 0);
  const taxAmount = baseTax * (taxRate / 100);
  const grandTotal = baseTax + taxAmount;
  return { gross, after, globalDisc, baseTax, taxAmount, grandTotal };
}

// Resolve a client-specific unit price for a given sale item (service/product)
// prices: array of client price rows
// opts: { sale_type: 'service'|'product', code: item code to match, qty: number, date?: 'YYYY-MM-DD' }
export function matchClientPriceUnit(
  prices: Array<any>,
  opts: { sale_type?: string; code?: string; qty?: number; date?: string }
): number | null {
  if (!prices || !Array.isArray(prices)) return null;
  const saleType = (opts.sale_type || '').toLowerCase();
  const code = (opts.code || '').trim();
  const qty = Number(opts.qty || 0);
  if (!saleType || !code || qty <= 0) return null;
  const inDate = (row: any) => {
    const d = (opts.date || '').trim();
    if (!d) return true; // no date provided -> accept
    const today = new Date(d);
    if (isNaN(today.getTime())) return true;
    const sd = row?.start_date ? new Date(String(row.start_date).slice(0,10)) : null;
    const ed = row?.end_date ? new Date(String(row.end_date).slice(0,10)) : null;
    if (sd && today < sd) return false;
    if (ed && today > ed) return false;
    return true;
  };
  const candidates = prices.filter((p: any) => {
    const st = String(p?.sale_type || '').toLowerCase();
    const c = String(p?.code || '').trim();
    const minq = Number(p?.min_qty || 0);
    if (!c || c !== code) return false;
    if (saleType && st && st !== saleType) return false;
    if (qty < (isFinite(minq) ? minq : 0)) return false;
    if (!inDate(p)) return false;
    return true;
  });
  if (!candidates.length) return null;
  // Pick the most specific: highest min_qty, then most recent start_date
  candidates.sort((a: any, b: any) => {
    const am = Number(a?.min_qty || 0), bm = Number(b?.min_qty || 0);
    if (am !== bm) return bm - am;
    const as = a?.start_date ? new Date(String(a.start_date).slice(0,10)).getTime() : 0;
    const bs = b?.start_date ? new Date(String(b.start_date).slice(0,10)).getTime() : 0;
    return bs - as;
  });
  const unit = Number(candidates[0]?.unit_price);
  return isFinite(unit) ? unit : null;
}
