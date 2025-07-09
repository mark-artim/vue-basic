import Papa from 'papaparse';
import axios from '@/utils/axios';

const xrefMaps = {
  pn: {},   // EDS_PN -> HER_PN
  cus: {},  // EDS_CUSNUM -> CONV_CUSNUM
};

export const loadCrossReferences = async () => {
  try {
    const [pnFile, cusFile] = await Promise.all([
      axios.get('/wasabi/download', {
        params: { filename: 'data/uploads/EDS.PN.XREF.csv' },
        responseType: 'blob'
      }),
      axios.get('/wasabi/download', {
        params: { filename: 'data/uploads/EDS.CUS.XREF.csv' },
        responseType: 'blob'
      }),
    ]);

    // Convert blobs to text
    const [pnText, cusText] = await Promise.all([
      pnFile.data.text(),
      cusFile.data.text()
    ]);

    // Parse PN XREF
    const pnParsed = Papa.parse(pnText.trim(), { skipEmptyLines: true });
    const pnRows = pnParsed.data;
    const pnHeaderIndex = pnRows.findIndex(row => row[0]?.startsWith('EDS_PN'));
    console.log('[xrefLoader] Raw PN Rows Sample:', pnRows.slice(0, 10));
    console.log('[xrefLoader] PN Header Index:', pnHeaderIndex);
    const pnDataRows = pnRows.slice(pnHeaderIndex + 1);
        xrefMaps.pn = Object.fromEntries(
      pnDataRows
        .map(row => [row[0]?.trim(), row[1]?.trim()])
        .filter(([edsPn, herPn]) => edsPn && herPn)
    );

    // xrefMaps.pn = {};
    // pnDataRows.forEach(row => {
    //   const edsPn = row[0]?.trim();
    //   const herPn = row[1]?.trim();
    //   if (edsPn && herPn) {
    //     xrefMaps.pn[edsPn] = herPn;
    //   }
    // });
    // console.log('10 sample HER_PN keys from xrefMaps.pn:');
    console.log('[xrefLoader] Final xrefMaps.pn sample:', Object.entries(xrefMaps.pn).slice(0, 5));



    // Parse CUS XREF
    const cusParsed = Papa.parse(cusText.trim(), { skipEmptyLines: true });
    const cusRows = cusParsed.data;
    const cusHeaderIndex = cusRows.findIndex(row => row[0]?.startsWith('EDS_CUSNUM'));
    const cusDataRows = cusRows.slice(cusHeaderIndex + 1);
    xrefMaps.cus = {};
    cusDataRows.forEach(row => {
      const edsCus = row[0]?.trim();
      const convCus = row[1]?.trim();
      if (edsCus && convCus) {
        xrefMaps.cus[edsCus] = convCus;
      }
    });

    console.log('[xrefLoader] Loaded PN and CUS xrefs:', {
      pn: Object.keys(xrefMaps.pn).length,
      cus: Object.keys(xrefMaps.cus).length,
    });
  } catch (err) {
    console.error('[xrefLoader] Failed to load xref CSVs:', err);
  }
};

export const getHerPN = (edsPn) => xrefMaps.pn[edsPn];
export const getConvCUS = (edsCus) => xrefMaps.cus[edsCus];
export const getAllPNXrefs = () => xrefMaps.pn;
export const getAllCUSXrefs = () => xrefMaps.cus;
