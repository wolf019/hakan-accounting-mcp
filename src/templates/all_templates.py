"""
Embedded templates for invoice generation.
This ensures templates are always available regardless of package installation method.
"""

INVOICE_TEMPLATE = """<!doctype html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Invoice {{ invoice.invoice_number }}</title>
    <style>
        {{ css_content }}
    </style>
</head>
<body>
    {{ header_content }}
    {{ line_items_content }}
    {{ footer_content }}
</body>
</html>"""

HEADER_TEMPLATE = """<div class="invoice-container">
    <!-- Header -->
    <div class="header">
        <div class="logo-section">
            <svg class="logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 213.095 21.16" fill="#0d141a">
                <path d="M15.32 1.56L6.37 9.20L6.35 7.91L16.38 16.45L11.96 16.45L3.04 8.63L10.97 1.56L15.32 1.56ZM0 16.45L0 1.56L3.06 1.56L3.06 16.45L0 16.45ZM22.31 16.70L22.31 16.70Q20.61 16.70 19.22 15.95Q17.82 15.20 17.01 13.86Q16.19 12.51 16.19 10.74L16.19 10.74Q16.19 8.92 17.02 7.59Q17.85 6.26 19.26 5.51Q20.68 4.76 22.47 4.76L22.47 4.76Q24.45 4.76 25.66 5.55Q26.86 6.35 27.42 7.71Q27.97 9.06 27.97 10.74L27.97 10.74Q27.97 11.75 27.65 12.80Q27.32 13.85 26.66 14.73Q25.99 15.62 24.91 16.16Q23.83 16.70 22.31 16.70ZM23.28 14.40L23.28 14.40Q24.63 14.40 25.62 13.94Q26.61 13.48 27.14 12.65Q27.67 11.82 27.67 10.74L27.67 10.74Q27.67 9.57 27.13 8.75Q26.59 7.94 25.61 7.51Q24.63 7.08 23.28 7.08L23.28 7.08Q21.37 7.08 20.31 8.08Q19.25 9.09 19.25 10.74L19.25 10.74Q19.25 11.85 19.76 12.66Q20.26 13.48 21.17 13.94Q22.08 14.40 23.28 14.40ZM27.67 13.50L27.67 5.01L30.66 5.01L30.66 16.45L27.88 16.45Q27.88 16.45 27.82 16.00Q27.76 15.55 27.71 14.86Q27.67 14.17 27.67 13.50L27.67 13.50ZM38.94 16.70L38.94 16.70Q37.24 16.70 35.85 15.95Q34.45 15.20 33.64 13.86Q32.82 12.51 32.82 10.74L32.82 10.74Q32.82 8.92 33.65 7.59Q34.48 6.26 35.89 5.51Q37.31 4.76 39.10 4.76L39.10 4.76Q41.08 4.76 42.29 5.55Q43.49 6.35 44.05 7.71Q44.60 9.06 44.60 10.74L44.60 10.74Q44.60 11.75 44.28 12.80Q43.95 13.85 43.29 14.73Q42.62 15.62 41.54 16.16Q40.46 16.70 38.94 16.70ZM39.91 14.40L39.91 14.40Q41.26 14.40 42.25 13.94Q43.24 13.48 43.77 12.65Q44.30 11.82 44.30 10.74L44.30 10.74Q44.30 9.57 43.76 8.75Q43.22 7.94 42.24 7.51Q41.26 7.08 39.91 7.08L39.91 7.08Q38.00 7.08 36.94 8.08Q35.88 9.09 35.88 10.74L35.88 10.74Q35.88 11.85 36.39 12.66Q36.89 13.48 37.80 13.94Q38.71 14.40 39.91 14.40ZM44.30 13.50L44.30 5.01L47.29 5.01L47.29 16.45L44.51 16.45Q44.51 16.45 44.45 16.00Q44.39 15.55 44.34 14.86Q44.30 14.17 44.30 13.50L44.30 13.50ZM50.00 16.45L50.00 5.01L52.99 5.01L52.99 16.45L50.00 16.45ZM57.38 4.76L57.38 7.47Q56.10 7.47 55.15 7.97Q54.21 8.46 53.64 9.18Q53.06 9.89 52.83 10.56L52.83 10.56L52.81 9.29Q52.83 9.02 52.99 8.48Q53.15 7.94 53.48 7.30Q53.80 6.67 54.33 6.08Q54.85 5.50 55.61 5.13Q56.37 4.76 57.38 4.76L57.38 4.76ZM69.64 12.65L69.64 12.65L72.54 12.65Q72.36 13.82 71.56 14.74Q70.77 15.66 69.41 16.19Q68.06 16.72 66.10 16.72L66.10 16.72Q63.92 16.72 62.24 16.02Q60.56 15.32 59.62 13.98Q58.67 12.65 58.67 10.76L58.67 10.76Q58.67 8.88 59.59 7.53Q60.51 6.19 62.16 5.47Q63.80 4.76 66.01 4.76L66.01 4.76Q68.26 4.76 69.76 5.47Q71.25 6.19 71.98 7.62Q72.70 9.06 72.59 11.29L72.59 11.29L61.69 11.29Q61.80 12.17 62.34 12.88Q62.88 13.59 63.81 14.01Q64.75 14.42 66.03 14.42L66.03 14.42Q67.46 14.42 68.41 13.93Q69.37 13.43 69.64 12.65ZM65.87 7.04L65.87 7.04Q64.22 7.04 63.18 7.76Q62.15 8.49 61.85 9.55L61.85 9.55L69.62 9.55Q69.51 8.39 68.53 7.72Q67.55 7.04 65.87 7.04ZM95.08 11.09L98.12 11.09Q97.91 12.88 96.85 14.14Q95.80 15.41 93.98 16.08Q92.16 16.74 89.65 16.74L89.65 16.74Q87.56 16.74 85.82 16.26Q84.09 15.78 82.83 14.81Q81.58 13.85 80.89 12.41Q80.20 10.97 80.20 9.04L80.20 9.04Q80.20 7.11 80.89 5.66Q81.58 4.21 82.83 3.23Q84.09 2.25 85.82 1.76Q87.56 1.27 89.65 1.27L89.65 1.27Q92.16 1.27 93.99 1.96Q95.82 2.65 96.88 3.92Q97.93 5.20 98.12 7.02L98.12 7.02L95.08 7.02Q94.78 6.05 94.08 5.35Q93.38 4.65 92.28 4.28Q91.17 3.91 89.65 3.91L89.65 3.91Q87.77 3.91 86.34 4.50Q84.92 5.08 84.13 6.22Q83.35 7.36 83.35 9.04L83.35 9.04Q83.35 10.70 84.13 11.82Q84.92 12.95 86.34 13.54Q87.77 14.12 89.65 14.12L89.65 14.12Q91.17 14.12 92.26 13.75Q93.36 13.39 94.06 12.70Q94.76 12.01 95.08 11.09L95.08 11.09ZM107.46 16.72L107.46 16.72Q105.29 16.72 103.65 16.03Q102.01 15.34 101.09 14.02Q100.17 12.70 100.17 10.76L100.17 10.76Q100.17 8.83 101.09 7.49Q102.01 6.14 103.65 5.45Q105.29 4.76 107.46 4.76L107.46 4.76Q109.62 4.76 111.24 5.45Q112.86 6.14 113.78 7.49Q114.70 8.83 114.70 10.76L114.70 10.76Q114.70 12.70 113.78 14.02Q112.86 15.34 111.24 16.03Q109.62 16.72 107.46 16.72ZM107.46 14.42L107.46 14.42Q108.65 14.42 109.61 14.00Q110.56 13.57 111.11 12.75Q111.67 11.94 111.67 10.76L111.67 10.76Q111.67 9.59 111.11 8.75Q110.56 7.91 109.62 7.47Q108.67 7.04 107.46 7.04L107.46 7.04Q106.26 7.04 105.29 7.47Q104.33 7.91 103.76 8.74Q103.20 9.57 103.20 10.76L103.20 10.76Q103.20 11.94 103.75 12.75Q104.31 13.57 105.27 14.00Q106.24 14.42 107.46 14.42ZM116.91 16.45L116.91 5.01L119.90 5.01L119.90 16.45L116.91 16.45ZM125.21 4.76L125.21 4.76Q126.27 4.76 127.17 5.04Q128.06 5.31 128.73 5.89Q129.40 6.46 129.77 7.35Q130.13 8.23 130.13 9.45L130.13 9.45L130.13 16.45L127.14 16.45L127.14 9.98Q127.14 8.53 126.44 7.85Q125.74 7.18 124.15 7.18L124.15 7.18Q122.96 7.18 121.99 7.64Q121.03 8.10 120.43 8.80Q119.83 9.50 119.74 10.26L119.74 10.26L119.72 9.09Q119.83 8.28 120.24 7.52Q120.66 6.76 121.36 6.13Q122.06 5.50 123.03 5.13Q123.99 4.76 125.21 4.76ZM132.39 12.65L132.39 12.65L135.15 12.65Q135.40 13.43 136.19 13.93Q136.99 14.42 138.28 14.42L138.28 14.42Q139.15 14.42 139.63 14.26Q140.12 14.10 140.30 13.79Q140.48 13.48 140.48 13.09L140.48 13.09Q140.48 12.60 140.19 12.34Q139.89 12.07 139.26 11.91Q138.64 11.75 137.68 11.62L137.68 11.62Q136.71 11.45 135.81 11.22Q134.92 10.99 134.23 10.61Q133.54 10.23 133.14 9.65Q132.73 9.06 132.73 8.21L132.73 8.21Q132.73 7.38 133.14 6.74Q133.54 6.10 134.26 5.66Q134.99 5.22 135.96 4.99Q136.94 4.76 138.07 4.76L138.07 4.76Q139.77 4.76 140.90 5.26Q142.02 5.75 142.59 6.64Q143.15 7.52 143.15 8.67L143.15 8.67L140.51 8.67Q140.32 7.82 139.77 7.44Q139.22 7.06 138.07 7.06L138.07 7.06Q136.94 7.06 136.37 7.41Q135.79 7.75 135.79 8.35L135.79 8.35Q135.79 8.83 136.15 9.10Q136.50 9.36 137.21 9.52Q137.91 9.68 138.97 9.87L138.97 9.87Q139.86 10.05 140.68 10.28Q141.50 10.51 142.14 10.87Q142.78 11.22 143.16 11.81Q143.54 12.40 143.54 13.29L143.54 13.29Q143.54 14.40 142.91 15.16Q142.28 15.92 141.10 16.32Q139.93 16.72 138.30 16.72L138.30 16.72Q136.85 16.72 135.80 16.41Q134.76 16.10 134.07 15.61Q133.38 15.11 133.00 14.55Q132.62 13.98 132.48 13.48Q132.34 12.97 132.39 12.65ZM159.04 5.01L159.04 16.45L156.06 16.45L156.06 5.01L159.04 5.01ZM156.22 10.95L156.22 10.95L156.24 11.73Q156.19 12.05 156.01 12.66Q155.82 13.27 155.45 13.96Q155.07 14.65 154.47 15.28Q153.87 15.92 153.00 16.32Q152.12 16.72 150.93 16.72L150.93 16.72Q149.98 16.72 149.07 16.49Q148.17 16.26 147.43 15.72Q146.69 15.18 146.26 14.26Q145.82 13.34 145.82 11.94L145.82 11.94L145.82 5.01L148.81 5.01L148.81 11.43Q148.81 12.54 149.17 13.17Q149.52 13.80 150.21 14.05Q150.90 14.31 151.85 14.31L151.85 14.31Q153.09 14.31 153.98 13.77Q154.88 13.23 155.45 12.44Q156.01 11.66 156.22 10.95ZM161.99 16.45L161.99 0.41L164.98 0.41L164.98 16.45L161.99 16.45ZM166.73 7.34L166.73 5.01L175.60 5.01L175.60 7.34L166.73 7.34ZM169.67 16.45L169.67 1.89L172.66 1.89L172.66 16.45L169.67 16.45ZM177.47 0L180.94 0L180.94 2.62L177.47 2.62L177.47 0ZM177.70 16.45L177.70 5.01L180.69 5.01L180.69 16.45L177.70 16.45ZM183.68 16.45L183.68 5.01L186.67 5.01L186.67 16.45L183.68 16.45ZM191.98 4.76L191.98 4.76Q193.04 4.76 193.94 5.04Q194.83 5.31 195.50 5.89Q196.17 6.46 196.53 7.35Q196.90 8.23 196.90 9.45L196.90 9.45L196.90 16.45L193.91 16.45L193.91 9.98Q193.91 8.53 193.21 7.85Q192.51 7.18 190.92 7.18L190.92 7.18Q189.73 7.18 188.76 7.64Q187.79 8.10 187.20 8.80Q186.60 9.50 186.51 10.26L186.51 10.26L186.48 9.09Q186.60 8.28 187.01 7.52Q187.43 6.76 188.13 6.13Q188.83 5.50 189.80 5.13Q190.76 4.76 191.98 4.76ZM205.32 14.70L205.32 14.70Q203.46 14.70 202.04 14.13Q200.63 13.57 199.85 12.47Q199.06 11.36 199.06 9.80L199.06 9.80Q199.06 8.26 199.82 7.13Q200.58 6.00 202.00 5.38Q203.41 4.76 205.32 4.76L205.32 4.76Q205.85 4.76 206.34 4.83Q206.84 4.90 207.32 5.01L207.32 5.01L213.09 5.04L213.09 7.29Q211.92 7.31 210.71 7.00Q209.51 6.69 208.59 6.33L208.59 6.33L208.52 6.16Q209.30 6.53 209.99 7.07Q210.68 7.61 211.11 8.31Q211.53 9.02 211.53 9.94L211.53 9.94Q211.53 11.43 210.77 12.50Q210.01 13.57 208.62 14.13Q207.23 14.70 205.32 14.70ZM212.15 21.16L209.16 21.16L209.16 20.61Q209.16 19.55 208.48 19.14Q207.80 18.72 206.63 18.72L206.63 18.72L203.07 18.72Q202.03 18.72 201.33 18.56Q200.63 18.40 200.21 18.10Q199.80 17.80 199.62 17.40Q199.43 17.00 199.43 16.54L199.43 16.54Q199.43 15.62 200.03 15.15Q200.63 14.67 201.64 14.51Q202.65 14.35 203.87 14.44L203.87 14.44L205.32 14.70Q203.87 14.74 203.17 14.94Q202.47 15.13 202.47 15.71L202.47 15.71Q202.47 16.05 202.74 16.25Q203.02 16.45 203.53 16.45L203.53 16.45L207.28 16.45Q208.82 16.45 209.91 16.78Q211.00 17.11 211.58 17.91Q212.15 18.70 212.15 20.08L212.15 20.08L212.15 21.16ZM205.32 12.54L205.32 12.54Q206.31 12.54 207.06 12.21Q207.80 11.89 208.22 11.28Q208.63 10.67 208.63 9.82L208.63 9.82Q208.63 8.95 208.22 8.33Q207.80 7.71 207.07 7.37Q206.33 7.04 205.32 7.04L205.32 7.04Q204.33 7.04 203.57 7.37Q202.81 7.71 202.40 8.33Q201.99 8.95 201.99 9.82L201.99 9.82Q201.99 10.67 202.40 11.28Q202.81 11.89 203.56 12.21Q204.31 12.54 205.32 12.54Z"/>
            </svg>
        </div>
        <div class="invoice-info">
            <div class="invoice-title">INVOICE</div>
        </div>
    </div>

    <!-- Invoice Details and Customer Info -->
    <div class="parties-section">
        <div class="party-block">
            <div class="party-info">
                <p><strong>Invoice Number:</strong> {{ invoice.invoice_number }}</p>
                <p><strong>Invoice Date:</strong> {{ invoice.issue_date|format_date("%Y-%m-%d") }}</p>
                <p><strong>Payment Terms:</strong> Net {{ invoice.payment_terms|default(30) }} days</p>
                <p><strong>Due Date:</strong> {{ invoice.due_date|format_date("%Y-%m-%d") }}</p>
            </div>
        </div>

        <div class="party-block">
            <div class="party-info">
                <p><strong>{{ customer.company if customer.company else customer.name }}</strong></p>
                {% if customer.org_number %}
                <p>Org.nr: {{ customer.org_number }}</p>
                {% endif %}
                {% if customer.street and customer.city %}
                <p>{{ customer.street }}</p>
                {% if customer.postal_code %}
                <p>{{ customer.postal_code }} {{ customer.city }}</p>
                {% else %}
                <p>{{ customer.city }}</p>
                {% endif %}
                {% if customer.country and customer.country.lower() != 'sweden' %}
                <p>{{ customer.country }}</p>
                {% endif %}
                {% elif customer.address %}
                <p>{{ customer.address|replace('\\n', '<br>')|safe }}</p>
                {% endif %}
                {% if customer.vat_number %}
                <p style="margin-top: 30px;">VAT: {{ customer.vat_number }}</p>
                {% endif %}
                {% if customer.contact_person %}
                <p style="margin-top: 15px;">Attn: {{ customer.contact_person }}</p>
                {% endif %}
                <p>{{ customer.email }}</p>
            </div>
        </div>
    </div>"""

LINE_ITEMS_TEMPLATE = """    <!-- Line Items -->
    <div class="items-section">
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {% for item in line_items %}
                <tr>
                    <td class="item-description">{{ item.description }}</td>
                    <td>{{ item.quantity }}</td>
                    <td>{{ item.unit_price|format_currency }}</td>
                    <td>{{ item.total|format_currency }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Summary -->
    <div class="summary-section">
        <div class="summary-block">
            <div class="summary-row subtotal">
                <span class="summary-label">Subtotal</span>
                <span class="summary-value">{{ invoice.subtotal|format_currency }}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">VAT ({{ (invoice.tax_rate * 100)|int }}%)</span>
                <span class="summary-value">{{ invoice.tax_amount|format_currency }}</span>
            </div>
            <div class="summary-row total">
                <span class="summary-label">Total Due</span>
                <span class="summary-value">{{ invoice.total|format_currency }}</span>
            </div>
        </div>
    </div>

    {% if invoice.notes %}
    <!-- Notes -->
    <div class="notes-section">
        <div class="notes-header">Notes</div>
        <div class="notes-content">
            {{ invoice.notes }}
        </div>
    </div>
    {% endif %}"""

FOOTER_TEMPLATE = """    <!-- Footer -->
    <div class="footer">
        <div class="footer-content">
            <div class="footer-column">
                <h4 class="footer-heading">Company Information</h4>
                <p>{{ company.name }}</p>
                <p>{{ company.address|replace('\\n', '<br>')|safe }}</p>
                <p>Org.nr: {{ company.org_number }}</p>
                <p>VAT: {{ company.vat_number }}</p>
            </div>

            <div class="footer-column">
                <h4 class="footer-heading">Contact Information</h4>
                <p>{{ company.name }}</p>
                {% if company.phone %}
                <p>{{ company.phone }}</p>
                {% endif %}
                {% if company.email %}
                <p>{{ company.email }}</p>
                {% endif %}
                <p>www.tomkaare.tech</p>
            </div>

            <div class="footer-column">
                <h4 class="footer-heading">Payment Information</h4>
                <p>Bank: Länsförsäkringar</p>
                <p>BIC/SWIFT: ELLFSESS</p>
                <p>IBAN: SE29 9020 0000 0906 0830 3135</p>
                <p>Clearing: 9060</p>
                <p>Account: 83.031.35</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>Late payment interest will be charged at the current reference rate + 12% per annum</p>
        </div>
    </div>
</div><!-- End invoice-container -->"""

CSS_CONTENT = """@page {
    size: A4;
    margin: 0;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #0d141a;
    background-color: #ffffff;
    padding: 40px;
}

.invoice-container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
}

/* Header Section */
.header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 60px;
}

.logo-section {
    flex: 1;
    display: flex;
    align-items: center;
}

.logo {
    width: 300px;
    height: auto;
    margin-top: 12px;
}

.invoice-info {
    text-align: right;
    display: flex;
    align-items: center;
}

.invoice-title {
    font-size: 32px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #0d141a;
}

/* Company and Customer Info */
.parties-section {
    display: flex;
    gap: 60px;
    margin-bottom: 50px;
}

.party-block {
    flex: 1;
}

.party-block:last-child {
    margin-left: 100px;
}

.party-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #666;
    margin-bottom: 15px;
    font-weight: 500;
}

.party-info {
    font-size: 14px;
    line-height: 1.8;
}

.party-info strong {
    font-weight: 600;
    color: #0d141a;
}

.party-block:last-child .party-info p:first-child strong {
    font-size: 16px;
}

.party-info p {
    margin-bottom: 3px;
}

/* Table Section */
.items-section {
    margin-bottom: 20px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

thead {
    border-bottom: 2px solid #e5e7eb;
}

th {
    text-align: left;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
}

th:last-child,
td:last-child {
    text-align: right;
}

th:nth-child(2),
td:nth-child(2),
th:nth-child(3),
td:nth-child(3) {
    text-align: right;
}

tbody tr {
    border-bottom: 1px solid #f3f4f6;
}

tbody tr:hover {
    background-color: #f9fafb;
}

td {
    padding: 8px 20px;
    font-size: 14px;
}

.item-description {
    font-weight: 500;
    color: #0d141a;
}

/* Summary Section */
.summary-section {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 60px;
    margin-top: 0;
}

.summary-block {
    width: 350px;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 14px;
}

.summary-row.subtotal {
    border-bottom: 1px solid #e5e7eb;
}

.summary-row.total {
    border-top: 2px solid #d4c8a8;
    margin-top: 4px;
    padding-top: 8px;
    font-size: 20px;
    font-weight: 600;
    color: #0d141a;
}

.summary-row.total .summary-value {
    color: #0d141a;
}

.summary-label {
    color: #666;
}

.summary-value {
    font-weight: 500;
    color: #0d141a;
}

.payment-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}

.payment-item {
    display: flex;
    flex-direction: column;
}

.payment-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
    margin-bottom: 5px;
}

.payment-value {
    font-size: 16px;
    font-weight: 500;
    color: #0d141a;
}

.payment-reference {
    grid-column: span 2;
    padding: 15px;
    background-color: #e3f2fd;
    border-radius: 4px;
    border-left: 4px solid #0066ff;
    margin-top: 10px;
}

.payment-reference .payment-value {
    color: #0066ff;
}

/* Footer */
.footer {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 2px solid #e5e7eb;
}

.footer-content {
    display: grid;
    grid-template-columns: 1fr 1fr 1.2fr;
    gap: 30px;
    margin-bottom: 15px;
}

.footer-column {
    font-size: 12px;
    line-height: 1.4;
    color: #666;
}

.footer-heading {
    font-size: 13px;
    font-weight: 600;
    color: #0d141a;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.footer-column p {
    margin: 0;
    padding: 0.5px 0;
}

.footer-bottom {
    text-align: center;
    padding-top: 12px;
    border-top: 1px solid #e5e7eb;
    font-size: 11px;
    color: #999;
    font-style: italic;
}

/* Notes Section */
.notes-section {
    margin-bottom: 40px;
    padding: 15px;
    background-color: #f0ead9;
    border-radius: 8px;
    border-left: 4px solid #d4c8a8;
}

.notes-header {
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 6px;
    color: #4a453a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.notes-content {
    font-size: 12px;
    line-height: 1.4;
    color: #5a5445;
}

/* Reminder Alert Section */
.reminder-alert {
    background-color: #fff3cd;
    border: 2px solid #ffeaa7;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 40px;
    text-align: center;
}

.reminder-alert h2 {
    color: #e67e22;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 10px;
    letter-spacing: 0.05em;
}

.reminder-alert p {
    color: #8b4513;
    font-size: 16px;
    font-weight: 500;
    margin: 0;
}"""

# Payment Reminder Templates

REMINDER_TEMPLATE = """<!doctype html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Payment Reminder - {{ original_invoice.invoice_number }}</title>
    <style>
        {{ css_content }}
        .reminder-header {
            background-color: #ff6b6b;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .reminder-header h1 {
            margin: 0;
            font-size: 24px;
        }
        .overdue-notice {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .calculation-breakdown {
            background-color: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .legal-notice {
            background-color: #e9ecef;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #6c757d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    {{ header_content }}
    {{ reminder_content }}
    {{ footer_content }}
</body>
</html>"""

REMINDER_HEADER_TEMPLATE = """<div class="invoice-container">
    <!-- Header -->
    <div class="header">
        <div class="logo-section">
            <svg class="logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 213.095 21.16" fill="#0d141a">
                <path d="M15.32 1.56L6.37 9.20L6.35 7.91L16.38 16.45L11.96 16.45L3.04 8.63L10.97 1.56L15.32 1.56ZM0 16.45L0 1.56L3.06 1.56L3.06 16.45L0 16.45ZM22.31 16.70L22.31 16.70Q20.61 16.70 19.22 15.95Q17.82 15.20 17.01 13.86Q16.19 12.51 16.19 10.74L16.19 10.74Q16.19 8.92 17.02 7.59Q17.85 6.26 19.26 5.51Q20.68 4.76 22.47 4.76L22.47 4.76Q24.45 4.76 25.66 5.55Q26.86 6.35 27.42 7.71Q27.97 9.06 27.97 10.74L27.97 10.74Q27.97 11.75 27.65 12.80Q27.32 13.85 26.66 14.73Q25.99 15.62 24.91 16.16Q23.83 16.70 22.31 16.70ZM23.28 14.40L23.28 14.40Q24.63 14.40 25.62 13.94Q26.61 13.48 27.14 12.65Q27.67 11.82 27.67 10.74L27.67 10.74Q27.67 9.57 27.13 8.75Q26.59 7.94 25.61 7.51Q24.63 7.08 23.28 7.08L23.28 7.08Q21.37 7.08 20.31 8.08Q19.25 9.09 19.25 10.74L19.25 10.74Q19.25 11.85 19.76 12.66Q20.26 13.48 21.17 13.94Q22.08 14.40 23.28 14.40ZM27.67 13.50L27.67 5.01L30.66 5.01L30.66 16.45L27.88 16.45Q27.88 16.45 27.82 16.00Q27.76 15.55 27.71 14.86Q27.67 14.17 27.67 13.50L27.67 13.50ZM38.94 16.70L38.94 16.70Q37.24 16.70 35.85 15.95Q34.45 15.20 33.64 13.86Q32.82 12.51 32.82 10.74L32.82 10.74Q32.82 8.92 33.65 7.59Q34.48 6.26 35.89 5.51Q37.31 4.76 39.10 4.76L39.10 4.76Q41.08 4.76 42.29 5.55Q43.49 6.35 44.05 7.71Q44.60 9.06 44.60 10.74L44.60 10.74Q44.60 11.75 44.28 12.80Q43.95 13.85 43.29 14.73Q42.62 15.62 41.54 16.16Q40.46 16.70 38.94 16.70ZM39.91 14.40L39.91 14.40Q41.26 14.40 42.25 13.94Q43.24 13.48 43.77 12.65Q44.30 11.82 44.30 10.74L44.30 10.74Q44.30 9.57 43.76 8.75Q43.22 7.94 42.24 7.51Q41.26 7.08 39.91 7.08L39.91 7.08Q38.00 7.08 36.94 8.08Q35.88 9.09 35.88 10.74L35.88 10.74Q35.88 11.85 36.39 12.66Q36.89 13.48 37.80 13.94Q38.71 14.40 39.91 14.40ZM44.30 13.50L44.30 5.01L47.29 5.01L47.29 16.45L44.51 16.45Q44.51 16.45 44.45 16.00Q44.39 15.55 44.34 14.86Q44.30 14.17 44.30 13.50L44.30 13.50ZM50.00 16.45L50.00 5.01L52.99 5.01L52.99 16.45L50.00 16.45ZM57.38 4.76L57.38 7.47Q56.10 7.47 55.15 7.97Q54.21 8.46 53.64 9.18Q53.06 9.89 52.83 10.56L52.83 10.56L52.81 9.29Q52.83 9.02 52.99 8.48Q53.15 7.94 53.48 7.30Q53.80 6.67 54.33 6.08Q54.85 5.50 55.61 5.13Q56.37 4.76 57.38 4.76L57.38 4.76ZM69.64 12.65L69.64 12.65L72.54 12.65Q72.36 13.82 71.56 14.74Q70.77 15.66 69.41 16.19Q68.06 16.72 66.10 16.72L66.10 16.72Q63.92 16.72 62.24 16.02Q60.56 15.32 59.62 13.98Q58.67 12.65 58.67 10.76L58.67 10.76Q58.67 8.88 59.59 7.53Q60.51 6.19 62.16 5.47Q63.80 4.76 66.01 4.76L66.01 4.76Q68.26 4.76 69.76 5.47Q71.25 6.19 71.98 7.62Q72.70 9.06 72.59 11.29L72.59 11.29L61.69 11.29Q61.80 12.17 62.34 12.88Q62.88 13.59 63.81 14.01Q64.75 14.42 66.03 14.42L66.03 14.42Q67.46 14.42 68.41 13.93Q69.37 13.43 69.64 12.65ZM65.87 7.04L65.87 7.04Q64.22 7.04 63.18 7.76Q62.15 8.49 61.85 9.55L61.85 9.55L69.62 9.55Q69.51 8.39 68.53 7.72Q67.55 7.04 65.87 7.04ZM95.08 11.09L98.12 11.09Q97.91 12.88 96.85 14.14Q95.80 15.41 93.98 16.08Q92.16 16.74 89.65 16.74L89.65 16.74Q87.56 16.74 85.82 16.26Q84.09 15.78 82.83 14.81Q81.58 13.85 80.89 12.41Q80.20 10.97 80.20 9.04L80.20 9.04Q80.20 7.11 80.89 5.66Q81.58 4.21 82.83 3.23Q84.09 2.25 85.82 1.76Q87.56 1.27 89.65 1.27L89.65 1.27Q92.16 1.27 93.99 1.96Q95.82 2.65 96.88 3.92Q97.93 5.20 98.12 7.02L98.12 7.02L95.08 7.02Q94.78 6.05 94.08 5.35Q93.38 4.65 92.28 4.28Q91.17 3.91 89.65 3.91L89.65 3.91Q87.77 3.91 86.34 4.50Q84.92 5.08 84.13 6.22Q83.35 7.36 83.35 9.04L83.35 9.04Q83.35 10.70 84.13 11.82Q84.92 12.95 86.34 13.54Q87.77 14.12 89.65 14.12L89.65 14.12Q91.17 14.12 92.26 13.75Q93.36 13.39 94.06 12.70Q94.76 12.01 95.08 11.09L95.08 11.09ZM107.46 16.72L107.46 16.72Q105.29 16.72 103.65 16.03Q102.01 15.34 101.09 14.02Q100.17 12.70 100.17 10.76L100.17 10.76Q100.17 8.83 101.09 7.49Q102.01 6.14 103.65 5.45Q105.29 4.76 107.46 4.76L107.46 4.76Q109.62 4.76 111.24 5.45Q112.86 6.14 113.78 7.49Q114.70 8.83 114.70 10.76L114.70 10.76Q114.70 12.70 113.78 14.02Q112.86 15.34 111.24 16.03Q109.62 16.72 107.46 16.72ZM107.46 14.42L107.46 14.42Q108.65 14.42 109.61 14.00Q110.56 13.57 111.11 12.75Q111.67 11.94 111.67 10.76L111.67 10.76Q111.67 9.59 111.11 8.75Q110.56 7.91 109.62 7.47Q108.67 7.04 107.46 7.04L107.46 7.04Q106.26 7.04 105.29 7.47Q104.33 7.91 103.76 8.74Q103.20 9.57 103.20 10.76L103.20 10.76Q103.20 11.94 103.75 12.75Q104.31 13.57 105.27 14.00Q106.24 14.42 107.46 14.42ZM116.91 16.45L116.91 5.01L119.90 5.01L119.90 16.45L116.91 16.45ZM125.21 4.76L125.21 4.76Q126.27 4.76 127.17 5.04Q128.06 5.31 128.73 5.89Q129.40 6.46 129.77 7.35Q130.13 8.23 130.13 9.45L130.13 9.45L130.13 16.45L127.14 16.45L127.14 9.98Q127.14 8.53 126.44 7.85Q125.74 7.18 124.15 7.18L124.15 7.18Q122.96 7.18 121.99 7.64Q121.03 8.10 120.43 8.80Q119.83 9.50 119.74 10.26L119.74 10.26L119.72 9.09Q119.83 8.28 120.24 7.52Q120.66 6.76 121.36 6.13Q122.06 5.50 123.03 5.13Q123.99 4.76 125.21 4.76ZM132.39 12.65L132.39 12.65L135.15 12.65Q135.40 13.43 136.19 13.93Q136.99 14.42 138.28 14.42L138.28 14.42Q139.15 14.42 139.63 14.26Q140.12 14.10 140.30 13.79Q140.48 13.48 140.48 13.09L140.48 13.09Q140.48 12.60 140.19 12.34Q139.89 12.07 139.26 11.91Q138.64 11.75 137.68 11.62L137.68 11.62Q136.71 11.45 135.81 11.22Q134.92 10.99 134.23 10.61Q133.54 10.23 133.14 9.65Q132.73 9.06 132.73 8.21L132.73 8.21Q132.73 7.38 133.14 6.74Q133.54 6.10 134.26 5.66Q134.99 5.22 135.96 4.99Q136.94 4.76 138.07 4.76L138.07 4.76Q139.77 4.76 140.90 5.26Q142.02 5.75 142.59 6.64Q143.15 7.52 143.15 8.67L143.15 8.67L140.51 8.67Q140.32 7.82 139.77 7.44Q139.22 7.06 138.07 7.06L138.07 7.06Q136.94 7.06 136.37 7.41Q135.79 7.75 135.79 8.35L135.79 8.35Q135.79 8.83 136.15 9.10Q136.50 9.36 137.21 9.52Q137.91 9.68 138.97 9.87L138.97 9.87Q139.86 10.05 140.68 10.28Q141.50 10.51 142.14 10.87Q142.78 11.22 143.16 11.81Q143.54 12.40 143.54 13.29L143.54 13.29Q143.54 14.40 142.91 15.16Q142.28 15.92 141.10 16.32Q139.93 16.72 138.30 16.72L138.30 16.72Q136.85 16.72 135.80 16.41Q134.76 16.10 134.07 15.61Q133.38 15.11 133.00 14.55Q132.62 13.98 132.48 13.48Q132.34 12.97 132.39 12.65ZM159.04 5.01L159.04 16.45L156.06 16.45L156.06 5.01L159.04 5.01ZM156.22 10.95L156.22 10.95L156.24 11.73Q156.19 12.05 156.01 12.66Q155.82 13.27 155.45 13.96Q155.07 14.65 154.47 15.28Q153.87 15.92 153.00 16.32Q152.12 16.72 150.93 16.72L150.93 16.72Q149.98 16.72 149.07 16.49Q148.17 16.26 147.43 15.72Q146.69 15.18 146.26 14.26Q145.82 13.34 145.82 11.94L145.82 11.94L145.82 5.01L148.81 5.01L148.81 11.43Q148.81 12.54 149.17 13.17Q149.52 13.80 150.21 14.05Q150.90 14.31 151.85 14.31L151.85 14.31Q153.09 14.31 153.98 13.77Q154.88 13.23 155.45 12.44Q156.01 11.66 156.22 10.95ZM161.99 16.45L161.99 0.41L164.98 0.41L164.98 16.45L161.99 16.45ZM166.73 7.34L166.73 5.01L175.60 5.01L175.60 7.34L166.73 7.34ZM169.67 16.45L169.67 1.89L172.66 1.89L172.66 16.45L169.67 16.45ZM177.47 0L180.94 0L180.94 2.62L177.47 2.62L177.47 0ZM177.70 16.45L177.70 5.01L180.69 5.01L180.69 16.45L177.70 16.45ZM183.68 16.45L183.68 5.01L186.67 5.01L186.67 16.45L183.68 16.45ZM191.98 4.76L191.98 4.76Q193.04 4.76 193.94 5.04Q194.83 5.31 195.50 5.89Q196.17 6.46 196.53 7.35Q196.90 8.23 196.90 9.45L196.90 9.45L196.90 16.45L193.91 16.45L193.91 9.98Q193.91 8.53 193.21 7.85Q192.51 7.18 190.92 7.18L190.92 7.18Q189.73 7.18 188.76 7.64Q187.79 8.10 187.20 8.80Q186.60 9.50 186.51 10.26L186.51 10.26L186.48 9.09Q186.60 8.28 187.01 7.52Q187.43 6.76 188.13 6.13Q188.83 5.50 189.80 5.13Q190.76 4.76 191.98 4.76ZM205.32 14.70L205.32 14.70Q203.46 14.70 202.04 14.13Q200.63 13.57 199.85 12.47Q199.06 11.36 199.06 9.80L199.06 9.80Q199.06 8.26 199.82 7.13Q200.58 6.00 202.00 5.38Q203.41 4.76 205.32 4.76L205.32 4.76Q205.85 4.76 206.34 4.83Q206.84 4.90 207.32 5.01L207.32 5.01L213.09 5.04L213.09 7.29Q211.92 7.31 210.71 7.00Q209.51 6.69 208.59 6.33L208.59 6.33L208.52 6.16Q209.30 6.53 209.99 7.07Q210.68 7.61 211.11 8.31Q211.53 9.02 211.53 9.94L211.53 9.94Q211.53 11.43 210.77 12.50Q210.01 13.57 208.62 14.13Q207.23 14.70 205.32 14.70ZM212.15 21.16L209.16 21.16L209.16 20.61Q209.16 19.55 208.48 19.14Q207.80 18.72 206.63 18.72L206.63 18.72L203.07 18.72Q202.03 18.72 201.33 18.56Q200.63 18.40 200.21 18.10Q199.80 17.80 199.62 17.40Q199.43 17.00 199.43 16.54L199.43 16.54Q199.43 15.62 200.03 15.15Q200.63 14.67 201.64 14.51Q202.65 14.35 203.87 14.44L203.87 14.44L205.32 14.70Q203.87 14.74 203.17 14.94Q202.47 15.13 202.47 15.71L202.47 15.71Q202.47 16.05 202.74 16.25Q203.02 16.45 203.53 16.45L203.53 16.45L207.28 16.45Q208.82 16.45 209.91 16.78Q211.00 17.11 211.58 17.91Q212.15 18.70 212.15 20.08L212.15 20.08L212.15 21.16ZM205.32 12.54L205.32 12.54Q206.31 12.54 207.06 12.21Q207.80 11.89 208.22 11.28Q208.63 10.67 208.63 9.82L208.63 9.82Q208.63 8.95 208.22 8.33Q207.80 7.71 207.07 7.37Q206.33 7.04 205.32 7.04L205.32 7.04Q204.33 7.04 203.57 7.37Q202.81 7.71 202.40 8.33Q201.99 8.95 201.99 9.82L201.99 9.82Q201.99 10.67 202.40 11.28Q202.81 11.89 203.56 12.21Q204.31 12.54 205.32 12.54Z"/>
            </svg>
        </div>
        <div class="invoice-info">
            <div class="invoice-title">PAYMENT REMINDER</div>
        </div>
    </div>

    <!-- Reminder Alert -->
    <div class="reminder-alert">
        <h2>⚠️ BETALNINGSPÅMINNELSE</h2>
        <p>Denna faktura är {{ reminder.days_overdue }} dagar försenad</p>
    </div>

    <!-- Reminder Details and Customer Info -->
    <div class="parties-section">
        <div class="party-block">
            <div class="party-label">Reminder Details</div>
            <div class="party-info">
                <p><strong>Reminder Number:</strong> {{ reminder.reminder_number }}</p>
                <p><strong>Reminder Date:</strong> {{ reminder.reminder_date|format_date("%Y-%m-%d") }}</p>
                <p><strong>Original Invoice:</strong> {{ original_invoice.invoice_number }}</p>
                <p><strong>Invoice Date:</strong> {{ original_invoice.issue_date|format_date("%Y-%m-%d") }}</p>
                <p><strong>Original Due Date:</strong> {{ original_invoice.due_date|format_date("%Y-%m-%d") }}</p>
            </div>
        </div>

        <div class="party-block">
            <div class="party-label">Bill To</div>
            <div class="party-info">
                <p><strong>{{ customer.company if customer.company else customer.name }}</strong></p>
                {% if customer.org_number %}
                <p>Org.nr: {{ customer.org_number }}</p>
                {% endif %}
                {% if customer.vat_number %}
                <p>VAT: {{ customer.vat_number }}</p>
                {% endif %}
                {% if customer.street and customer.city %}
                <p>{{ customer.street }}</p>
                {% if customer.postal_code %}
                <p>{{ customer.postal_code }} {{ customer.city }}</p>
                {% else %}
                <p>{{ customer.city }}</p>
                {% endif %}
                {% if customer.country and customer.country.lower() != 'sweden' %}
                <p>{{ customer.country }}</p>
                {% endif %}
                {% elif customer.address %}
                <p>{{ customer.address|replace('\\n', '<br>')|safe }}</p>
                {% endif %}
                {% if customer.contact_person %}
                <p style="margin-top: 10px;">Attn: {{ customer.contact_person }}</p>
                {% endif %}
                <p>{{ customer.email }}</p>
            </div>
        </div>
    </div>"""

REMINDER_CONTENT_TEMPLATE = """<div class="overdue-notice">
    <h3>⚠️ Försenad betalning</h3>
    <p>Vi har inte mottagit betalning för faktura <strong>{{ original_invoice.invoice_number }}</strong>
    som utfärdades {{ original_invoice.issue_date|format_date("%Y-%m-%d") }} med förfallodatum
    {{ original_invoice.due_date|format_date("%Y-%m-%d") }}.</p>

    <p>Enligt avtalsvillkor och svensk lag tillkommer nu dröjsmålsränta och avgifter
    som redovisas nedan.</p>
</div>

<div class="calculation-breakdown">
    <h3>Beräkning av skuld</h3>

    <table style="width: 100%; border-collapse: collapse;">
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;"><strong>Ursprungligt fakturabelopp:</strong></td>
            <td style="padding: 10px; text-align: right;">{{ reminder.original_amount|format_currency }}</td>
        </tr>
        {% if reminder.interest_amount > 0 %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;">Dröjsmålsränta ({{ reminder.interest_rate }}% årsränta):</td>
            <td style="padding: 10px; text-align: right;">{{ reminder.interest_amount|format_currency }}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd; font-size: 12px; color: #666;">
            <td style="padding: 5px 10px;">• Referensränta: {{ reminder.reference_rate }}%</td>
            <td style="padding: 5px 10px; text-align: right;">• {{ reminder.days_overdue }} dagar försenad</td>
        </tr>
        {% endif %}
        {% if reminder.reminder_fee > 0 %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;">Påminnelseavgift:</td>
            <td style="padding: 10px; text-align: right;">{{ reminder.reminder_fee|format_currency }}</td>
        </tr>
        {% endif %}
        {% if reminder.delay_compensation > 0 %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;">Dröjsmålsersättning:</td>
            <td style="padding: 10px; text-align: right;">{{ reminder.delay_compensation|format_currency }}</td>
        </tr>
        {% endif %}
        <tr style="border-top: 2px solid #2c3e50; font-weight: bold; font-size: 18px;">
            <td style="padding: 15px;"><strong>Totalt att betala:</strong></td>
            <td style="padding: 15px; text-align: right; color: #e74c3c;"><strong>{{ reminder.total_amount|format_currency }}</strong></td>
        </tr>
    </table>
</div>

<div class="legal-notice">
    <h4>Rättslig information</h4>
    <p><strong>Dröjsmålsränta:</strong> Enligt räntelagen tillkommer dröjsmålsränta från 30 dagar efter fakturadatum.
    Räntan beräknas enligt Riksbankens referensränta plus 8 procentenheter.</p>

    {% if reminder.customer_type.value == 'business' %}
    <p><strong>Dröjsmålsersättning:</strong> Som företagskund har vi rätt till schablonersättning på 450 SEK
    enligt räntelagen 6 § för första påminnelsen.</p>
    {% endif %}

    <p><strong>Fortsatta åtgärder:</strong> Om betalning inte sker inom 10 dagar från detta datum
    kommer ärendet att överlämnas till inkassobolag eller kronofogden, vilket medför ytterligare kostnader.</p>
</div>"""

REMINDER_FOOTER_TEMPLATE = """    <!-- Footer -->
    <div class="footer">
        <div class="footer-content">
            <div class="footer-column">
                <h4 class="footer-heading">Company Information</h4>
                <p>{{ company.name }}</p>
                <p>{{ company.address|replace('\\n', '<br>')|safe }}</p>
                <p>Org.nr: {{ company.org_number }}</p>
                <p>VAT: {{ company.vat_number }}</p>
            </div>

            <div class="footer-column">
                <h4 class="footer-heading">Contact Information</h4>
                <p>{{ company.name }}</p>
                {% if company.phone %}
                <p>{{ company.phone }}</p>
                {% endif %}
                {% if company.email %}
                <p>{{ company.email }}</p>
                {% endif %}
                <p>www.tomkaare.tech</p>
            </div>

            <div class="footer-column">
                <h4 class="footer-heading">Payment Information</h4>
                <p>Bank: Länsförsäkringar</p>
                <p>BIC/SWIFT: ELLFSESS</p>
                <p>IBAN: SE29 9020 0000 0906 0830 3135</p>
                <p>Clearing: 9060</p>
                <p>Account: 83.031.35</p>
                <p style="margin-top: 8px;"><strong>Amount Due:</strong> <span style="color: #e74c3c; font-weight: bold;">{{ reminder.total_amount|format_currency }}</span></p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>Late payment interest will be charged at the current reference rate + 12% per annum</p>
        </div>
    </div>
</div><!-- End invoice-container -->"""

# VAT Report Templates

VAT_REPORT_TEMPLATE = """<!doctype html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>VAT Report Q{{ quarter }} {{ year }}</title>
    <style>
        {{ css_content }}
        .vat-summary {
            background-color: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }
        .summary-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .summary-table th,
        .summary-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .summary-table th {
            background-color: #e9ecef;
            font-weight: bold;
            color: #2c3e50;
        }
        .summary-table td:last-child,
        .summary-table th:last-child {
            text-align: right;
        }
        .total-row {
            font-weight: bold;
            font-size: 1.1em;
            background-color: #e8f5e8;
            border-top: 2px solid #28a745;
        }
        .section-header {
            color: #2c3e50;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        .report-period {
            background-color: #e3f2fd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            text-align: center;
        }
        .expense-detail {
            margin-top: 30px;
        }
        .category-breakdown {
            margin: 20px 0;
        }
    </style>
</head>
<body>
    {{ header_content }}
    {{ vat_summary_content }}
    {{ sales_detail_content }}
    {{ expense_detail_content }}
    {{ footer_content }}
</body>
</html>"""

VAT_REPORT_HEADER_TEMPLATE = """<header>
    <div class="company-info">
        <h1>{{ company.name }}</h1>
        <p>{{ company.address|replace('\\n', '<br>')|safe }}</p>
        <p>Personnummer för enskild firma: {{ company.org_number }}</p>
        <p>Momsreg.nr: {{ company.vat_number }}</p>
        {% if company.email %}
        <p>Email: {{ company.email }}</p>
        {% endif %}
        {% if company.phone %}
        <p>Phone: {{ company.phone }}</p>
        {% endif %}
    </div>
    <div class="invoice-info">
        <h2>Momsdeklaration</h2>
        <p><strong>Period:</strong> Kvartal {{ quarter }} {{ year }}</p>
        <p><strong>Rapportdatum:</strong> {{ report_date|format_date("%Y-%m-%d") }}</p>
    </div>
</header>

<div class="report-period">
    <h2>Momsrapport - Kvartal {{ quarter }} {{ year }}</h2>
    <p><strong>Rapportperiod:</strong> {{ start_date|format_date("%Y-%m-%d") }} till {{ end_date|format_date("%Y-%m-%d") }}</p>
</div>"""

VAT_SUMMARY_TEMPLATE = """<section class="vat-summary">
    <h2>Sammanfattning</h2>
    <table class="summary-table">
        <thead>
            <tr>
                <th>Beskrivning</th>
                <th>Belopp (SEK)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Försäljning (exkl. moms)</td>
                <td>{{ total_sales|format_currency }}</td>
            </tr>
            <tr>
                <td>Utgående moms (försäljning)</td>
                <td>{{ output_vat|format_currency }}</td>
            </tr>
            <tr>
                <td>Inköp (exkl. moms)</td>
                <td>{{ total_purchases|format_currency }}</td>
            </tr>
            <tr>
                <td>Ingående moms (inköp)</td>
                <td>{{ input_vat|format_currency }}</td>
            </tr>
            <tr class="total-row">
                <td><strong>{% if net_vat >= 0 %}Moms att betala{% else %}Moms att få tillbaka{% endif %}</strong></td>
                <td><strong>{{ net_vat|abs|format_currency }}</strong></td>
            </tr>
        </tbody>
    </table>
</section>"""

VAT_SALES_DETAIL_TEMPLATE = """<section class="sales-detail">
    <h2 class="section-header">Försäljning ({{ invoice_count }} fakturor)</h2>

    {% if invoices %}
    <table class="summary-table">
        <thead>
            <tr>
                <th>Fakturanummer</th>
                <th>Kund</th>
                <th>Datum</th>
                <th>Netto</th>
                <th>Moms</th>
                <th>Totalt</th>
            </tr>
        </thead>
        <tbody>
            {% for invoice in invoices %}
            <tr>
                <td>{{ invoice.invoice_number }}</td>
                <td>{{ invoice.customer_name }}</td>
                <td>{{ invoice.issue_date|format_date("%Y-%m-%d") }}</td>
                <td>{{ invoice.subtotal|format_currency }}</td>
                <td>{{ invoice.tax_amount|format_currency }}</td>
                <td>{{ invoice.total|format_currency }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>Inga fakturor för denna period.</p>
    {% endif %}
</section>"""

VAT_EXPENSE_DETAIL_TEMPLATE = """<section class="expense-detail">
    <h2 class="section-header">Inköp ({{ expense_count }} utgifter)</h2>

    {% if expenses %}
    <div class="category-breakdown">
        <h3>Uppdelning per kategori:</h3>
        {% for category, data in expenses_by_category.items() %}
        <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
            <h4>{{ data.category_name }} ({{ data.count }} utgifter)</h4>
            <p>Netto: {{ data.net_amount|format_currency }} | Moms: {{ data.vat_amount|format_currency }} | Totalt: {{ data.total_amount|format_currency }}</p>
        </div>
        {% endfor %}
    </div>

    <table class="summary-table">
        <thead>
            <tr>
                <th>Datum</th>
                <th>Beskrivning</th>
                <th>Kategori</th>
                <th>Netto</th>
                <th>Moms</th>
                <th>Totalt</th>
            </tr>
        </thead>
        <tbody>
            {% for expense in expenses %}
            <tr>
                <td>{{ expense.expense_date|format_date("%Y-%m-%d") }}</td>
                <td>{{ expense.description }}</td>
                <td>{{ expense.category_name }}</td>
                <td>{{ (expense.amount - expense.vat_amount)|format_currency }}</td>
                <td>{{ expense.vat_amount|format_currency }}</td>
                <td>{{ expense.amount|format_currency }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>Inga avdragsgilla utgifter för denna period.</p>
    {% endif %}
</section>"""

VAT_REPORT_FOOTER_TEMPLATE = """<footer>
    <div class="legal-notice" style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <h4>Viktiga noteringar</h4>
        <ul>
            <li>Denna rapport baseras på bokförda transaktioner för angiven period</li>
            <li>Kontrollera att alla fakturor och utgifter är korrekt bokförda</li>
            <li>Momsdeklaration ska lämnas in senast månaden efter kvartalets slut</li>
            <li>Spara denna rapport som underlag för din momsdeklaration</li>
        </ul>
    </div>

    <div class="payment-info">
        <h3>Nästa steg:</h3>
        <ol>
            <li>Kontrollera att alla siffror stämmer med din bokföring</li>
            <li>Logga in på Skatteverkets webbplats (skatteverket.se)</li>
            <li>Fyll i din momsdeklaration med siffrorna från denna rapport</li>
            <li>{% if net_vat >= 0 %}Betala momsen senast förfallodagen{% else %}Moms kommer att betalas ut till ditt konto{% endif %}</li>
        </ol>
    </div>

    <div class="footer-text">
        <p><small>Rapport genererad {{ report_date|format_date("%Y-%m-%d %H:%M") }} av MCP Invoice Server</small></p>
    </div>
</footer>"""
