from flask import Flask, request, jsonify
import spacy

app = Flask(__name__)

# Load the pre-trained spaCy model
nlp = spacy.load("en_core_web_sm")

# Define a mapping of spaCy entity types to our custom categories
ENTITY_CATEGORY_MAPPING = {
    "DATE": "DATE_OF_BIRTH",
    "PERSON": "NAME_OF_CUSTOMER",
    "GPE": ["ADDRESS_OF_CUSTOMER", "PLACE_OF_BIRTH"],
    "CARDINAL": "CARDINAL",
    "DATE_OF_BIRTH": "DATE_OF_BIRTH",
    "NAME": "NAME_OF_CUSTOMER",
    "ADDRESS": "ADDRESS_OF_CUSTOMER",
    "CITY": "PLACE_OF_BIRTH",
    "COUNTRY": "PLACE_OF_BIRTH"
}

def keyValueMatchingModel(key, value):
    # First, try to categorize based on key patterns
    key_lower = key.lower()
    
    # Check for specific key patterns first
    if any(word in key_lower for word in ["wallet", "crypto", "blockchain"]):
        return "WALLET_ADDRESS"
    elif "passport" in key_lower or (("id" in key_lower or "identification" in key_lower) and "document" in key_lower):
        return "ID_DOCUMENT_NUMBER"
    elif "account" in key_lower or "customer id" in key_lower:
        return "CUSTOMER_ACCOUNT"
    elif any(word in key_lower for word in ["birth", "born", "birthday"]):
        return "DATE_OF_BIRTH"
    elif "name" in key_lower:
        return "NAME_OF_CUSTOMER"
    elif "address" in key_lower and "wallet" not in key_lower:  # Explicit check to avoid wallet address confusion
        return "ADDRESS_OF_CUSTOMER"
    
    # Process the key and value using spaCy for more complex cases
    doc = nlp(f"{key}: {value}")
    
    # Look for entities in both key and value
    for ent in doc.ents:
        # Map spaCy entity types to our custom categories
        if ent.label_ in ENTITY_CATEGORY_MAPPING:
            category = ENTITY_CATEGORY_MAPPING[ent.label_]
            
            # Handle special cases for CARDINAL type
            if ent.label_ == "CARDINAL":
                if is_wallet_address(value):
                    return "WALLET_ADDRESS"
                elif is_account_number(value):
                    return "CUSTOMER_ACCOUNT"
                elif is_id_document(value):
                    return "ID_DOCUMENT_NUMBER"
    
    # If no category found yet, try value-based heuristics
    if is_wallet_address(value):
        return "WALLET_ADDRESS"
    elif is_address(value):
        return "ADDRESS_OF_CUSTOMER"
    elif is_date(value):
        return "DATE_OF_BIRTH"
    elif is_name(value):
        return "NAME_OF_CUSTOMER"
    
    return None

def is_wallet_address(text):
    # Check if the text matches typical wallet address pattern
    return text.startswith("0x") and len(text) >= 40

def is_account_number(text):
    # Check if the text is a numeric string
    return text.isdigit() and len(text) >= 5

def is_id_document(text):
    # Check if the text matches typical ID document pattern (alphanumeric)
    return any(c.isalpha() for c in text) and any(c.isdigit() for c in text)

def is_name(text):
    # Check if text contains only letters and spaces
    return all(c.isalpha() or c.isspace() for c in text)

def is_address(text):
    # Check if text contains common address elements
    return "," in text and any(c.isdigit() for c in text)

def is_date(text):
    # Check if text matches common date formats
    return any(x in text for x in [".", "/", "-"]) and any(c.isdigit() for c in text)

@app.route('/categorize', methods=['POST'])
def categorize():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        categorized_data = {}
        
        for key, value in data.items():
            # Convert value to string if it's not already
            value_str = str(value)
            
            # Get category using the key-value matching model
            category = keyValueMatchingModel(key, value_str)
            
            if category:
                if category not in categorized_data:
                    categorized_data[category] = []
                categorized_data[category].append({
                    'key': key,
                    'value': value
                })
            else:
                if 'uncategorized' not in categorized_data:
                    categorized_data['uncategorized'] = []
                categorized_data['uncategorized'].append({
                    'key': key,
                    'value': value
                })
        
        return jsonify(categorized_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)