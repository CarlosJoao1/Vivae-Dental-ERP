import React from 'react'
import { useTranslation } from 'react-i18next'
import type { Line } from '@/api/sales'
import { calcGross, calcNet, computeGlobalDiscount } from '@/lib/pricing'

export default function TotalsSummary({ hdr, lines }:{ hdr:any; lines:Array<Partial<Line>|any> }){
  const { t } = useTranslation()
  const sumGross = (lines||[]).reduce((s, ln)=> s + calcGross(ln), 0)
  const sumAfterLine = (lines||[]).reduce((s, ln)=> s + calcNet(ln), 0)
  const globalDisc = computeGlobalDiscount(hdr, sumAfterLine)
  const baseTax = Math.max(0, sumAfterLine - (globalDisc||0))
  const taxAmount = baseTax * ((hdr?.tax_rate||0)/100)
  const grandTotal = baseTax + taxAmount
  return (
    <div className="text-right space-y-1">
      <div>{t('subtotal')||'Subtotal'}: {sumGross.toFixed(2)} {hdr?.currency}</div>
      <div>{t('line_discount')||'Line discount'}: {(sumGross - sumAfterLine).toFixed(2)} {hdr?.currency}</div>
      <div>{t('subtotal_after_discount')||'Subtotal'}: {sumAfterLine.toFixed(2)} {hdr?.currency}</div>
      {(((hdr?.discount_rate)||0) > 0 || (hdr as any)?.discount_amount) && (<div>{t('global_discount')||'Global discount'}: {globalDisc.toFixed(2)} {hdr?.currency}</div>)}
      <div>{t('tax')||'Tax'}: {taxAmount.toFixed(2)} {hdr?.currency}</div>
      <div className="font-semibold">{t('grand_total')||'Total'}: {grandTotal.toFixed(2)} {hdr?.currency}</div>
    </div>
  )
}

export function GrandTotal({ hdr, lines }:{ hdr:any; lines:Array<Partial<Line>|any> }){
  const { t } = useTranslation()
  const sumGross = (lines||[]).reduce((s, ln)=> s + calcGross(ln), 0)
  const sumAfterLine = (lines||[]).reduce((s, ln)=> s + calcNet(ln), 0)
  const globalDisc = computeGlobalDiscount(hdr, sumAfterLine)
  const baseTax = Math.max(0, sumAfterLine - (globalDisc||0))
  const taxAmount = baseTax * ((hdr?.tax_rate||0)/100)
  const grandTotal = baseTax + taxAmount
  return (<div className="text-lg font-semibold">{t('grand_total')||'Total'}: {grandTotal.toFixed(2)} {hdr?.currency}</div>)
}
