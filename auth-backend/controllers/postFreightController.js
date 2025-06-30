import fs from 'fs/promises';
import path from 'path';

export const postFreightHandler = async (req, res) => {
  try {
    const {
      invoiceNumber,
      totalFreight,
      shipVia,
      trackingNumber,
      weight,
      actualWeight,
      billAccount
    } = req.body;

    const lines = [];

    lines.push('[SHIPMENT]');
    lines.push(`OrdNum=${invoiceNumber}`);
    lines.push('Status=Save');
    lines.push('TotPkgs=1');
    lines.push(`TotFreight=${totalFreight}`);
    lines.push('TotHFee=0.00');
    lines.push('TotDValue=0.00');
    lines.push(`TotCharges=${totalFreight}`);
    lines.push(`ShipVia=${shipVia}`);
    lines.push('[PKG001]');
    lines.push(`TrackNum=${trackingNumber}`);
    lines.push(`BillFreight=${billAccount ? 'BillToCustomer' : 'Prepaid'}`);
    lines.push(`Weight=${weight}`);
    lines.push(`Actual Weight=${actualWeight}`);
    lines.push(`PkgFreight=${totalFreight}`);
    lines.push('HFee=0.00');
    lines.push(`PkgCharges=${totalFreight}`);
    if (billAccount) {
      lines.push(`BillAccnt=${billAccount}`);
    }

    const content = lines.join('\n');
    const filePath = 'C:/Users/mark.artim/OneDrive - Heritage Distribution Holdings/EclipseDownload/ADEOUT.0';

    await fs.writeFile(filePath, content, 'utf8');

    console.log('[postFreight] File written to:', filePath);

    res.json({ success: true, path: filePath });
  } catch (err) {
    console.error('[postFreight Error]:', err);
    res.status(500).json({ error: 'Failed to write freight export file' });
  }
};
