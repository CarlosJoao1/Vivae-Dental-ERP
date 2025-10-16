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
