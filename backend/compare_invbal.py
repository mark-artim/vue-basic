from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

print(app.url_map)   # <-- this will log all registered endpoints

# adjust to wherever your CSVs live
BASE_DIR = 'C:/Users/mark.artim/OneDrive - Heritage Distribution Holdings/EclipseDownload/'

@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'

@app.route('/api/compare-inv-bal', methods=['POST'])

def compare_inv_bal():
    data = request.get_json()
    conv_fn = data.get('conv_filename')
    eds_fn  = data.get('eds_filename')
    part_col = data.get('eds_part_col')

    if not all([conv_fn, eds_fn, part_col]):
        return jsonify(message="Missing one of: conv_filename, eds_filename or eds_part_col"), 400

    conv_path = os.path.join(BASE_DIR, conv_fn)
    eds_path  = os.path.join(BASE_DIR, eds_fn)
    print(f"conv_path: {conv_path}")
    print(f"eds_path: {eds_path}")
    if not os.path.isfile(conv_path) or not os.path.isfile(eds_path):
        return jsonify(message="One or both files not found"), 404

    try:
        conv_df = pd.read_csv(conv_path, encoding='windows-1252', skiprows=8, dtype=str)
        eds_df  = pd.read_csv(eds_path, encoding='windows-1252', skiprows=8,  dtype=str)
        print(">>> CONV DF columns:", conv_df.columns.tolist())
        print(">>> EDS  DF columns:",  eds_df.columns.tolist())
        print(">>> CONV DF sample:\n", conv_df.head(3))
        print(">>> EDS  DF sample:\n", eds_df.head(3))

        diffs = []
        for _, eds_row in eds_df.iterrows():
            part = eds_row.get('ECL_PN')
            if not part:
                continue

            match = conv_df[conv_df[part_col] == part]
            if match.empty:
                continue

            # grab the first matching row
            conv_row = match.iloc[0]

            # pull out the extra fields we want
            conv_ecl_pn     = conv_row.get('ECL_PN')
            matched_part_val = conv_row.get(part_col)

            # parse totals
            conv_val = conv_row.get('OH-TOTAL')
            eds_val  = eds_row.get('OH-TOTAL')
            try:
                c = float(conv_val)
                e = float(eds_val)
            except (ValueError, TypeError):
                continue

            if c != e:
                diffs.append({
                    'eds_ecl': part,              # the EDS file’s ECL_PN
                    'conv_ecl': conv_ecl_pn,      # the CONV file’s ECL_PN
                    'matched_val': matched_part_val,  # the value in the chosen column
                    'conv_total': c,
                    'eds_total':  e,
                    'diff':       c - e
                })
        return jsonify(differences=diffs)

    except Exception as ex:
        return jsonify(message=str(ex)), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
