import os
import requests
import html
import json
from flask import Flask, render_template, request

# --- Initialize Flask App ---
app = Flask(__name__)

# --- Your Original Helper Functions (Unchanged) ---
def parse_value(value_str):
    value_str = str(value_str).strip().upper()
    if not value_str:
        return 0
    multipliers = {
        'SX': 1e21, 'QI': 1e18, 'QA': 1e15, 'Q': 1e15,
        'T': 1e12, 'B': 1e9, 'M': 1e6, 'K': 1e3
    }
    for suffix in sorted(multipliers.keys(), key=len, reverse=True):
        if value_str.endswith(suffix):
            number_part = value_str[:-len(suffix)]
            multiplier = multipliers[suffix]
            try:
                value = float(number_part) * multiplier
                return int(value)
            except ValueError:
                return 0
    try:
        return int(float(value_str))
    except ValueError:
        return 0

def normalize_variant(v):
    v = v.lower().strip()
    variants = {
        "0": "All", "all": "All",
        "1": "Normal", "normal": "Normal",
        "2": "Shiny", "shiny": "Shiny",
        "3": "Mythic", "mythic": "Mythic",
        "4": "ShinyMythic", "shinymythic": "ShinyMythic"
    }
    return variants.get(v, None)

def fetch_data(search, variant):
    tries = [search.lower(), search.title(), search]
    for term in tries:
        s = term.replace(" ", "+")
        url = f"https://bgsi-kyc3.onrender.com/api/items?search={s}&variant={variant}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            raw = res.text
            # Use robust parsing in case the <pre> tag is missing
            if "<pre>" in raw:
                pre_data = raw.split("<pre>")[1].split("</pre>")[0]
            else:
                pre_data = raw
            
            data = json.loads(html.unescape(pre_data))
            if "pets" in data and data["pets"]:
                # Add the URL to each pet for display
                for pet in data["pets"]:
                    pet['link'] = url
                return data["pets"]
        except Exception as e:
            print(f"Error fetching or parsing data for {term} ({variant}): {e}") # For server-side logging
            continue
    return None

# --- Flask Web Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    total_value = 0
    results = []
    error_message = None
    # Keep the inputs in the form after submission
    search_input = ""
    variant_input = ""

    if request.method == 'POST':
        search_input = request.form.get('pets', '').strip()
        variant_input = request.form.get('variants', '').strip()

        if not search_input or not variant_input:
            error_message = "Pet name(s) and variant(s) cannot be blank."
        else:
            searches = [s.strip() for s in search_input.split(',')]
            raw_variants = [v.strip() for v in variant_input.split(',')]
            
            valid_variants = []
            for v_raw in raw_variants:
                norm_v = normalize_variant(v_raw)
                if norm_v:
                    if norm_v == "All":
                        valid_variants.extend(["Normal", "Shiny", "Mythic", "ShinyMythic"])
                    else:
                        valid_variants.append(norm_v)
            
            variants_to_try = list(dict.fromkeys(valid_variants)) # Remove duplicates

            if not variants_to_try:
                 error_message = "No valid variants were entered. Please use names like 'Normal', 'Shiny', or numbers '1', '2', etc."
            else:
                for search_term in searches:
                    for v in variants_to_try:
                        pets_found = fetch_data(search_term, v)
                        if pets_found:
                            for pet in pets_found:
                                pet_value = parse_value(pet.get('value', '0'))
                                pet['calculated_value'] = pet_value
                                total_value += pet_value
                                results.append(pet)
    
    # render_template will look for index.html in the 'templates' folder
    return render_template('index.html', 
                           results=results, 
                           total_value=total_value,
                           error=error_message,
                           search_input=search_input,
                           variant_input=variant_input)

# --- Run the App ---
if __name__ == "__main__":
    # This is for local development. Render will use Gunicorn instead.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)