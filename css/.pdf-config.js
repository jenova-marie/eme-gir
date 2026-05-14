module.exports = {
  stylesheet: ['prompt/.pdf-style.css'],
  pdf_options: {
    format: 'Letter',
    margin: { top: '28mm', bottom: '22mm', left: '20mm', right: '20mm' },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: `
      <div style="
        width: 100%;
        font-family: -apple-system, 'Helvetica Neue', sans-serif;
        font-size: 9pt;
        color: #0b3d66;
        padding: 4px 20mm 0 20mm;
        border-bottom: 1px solid #4a90c2;
        display: flex;
        justify-content: space-between;
        align-items: center;
      ">
        <span style="font-weight: 600; letter-spacing: 0.5px;">
          𒀭𒈹 <span style="color:#1565a0;" class="title"></span>
        </span>
        <span style="font-style: italic; color: #4a90c2;">𒊹 𒀭𒈹𒊏</span>
      </div>`,
    footerTemplate: `
      <div style="
        width: 100%;
        font-family: -apple-system, 'Helvetica Neue', sans-serif;
        font-size: 8pt;
        color: #4a90c2;
        padding: 0 20mm;
        text-align: center;
      ">
        Tablet <span class="pageNumber"></span> of <span class="totalPages"></span>
      </div>`,
  },
};
