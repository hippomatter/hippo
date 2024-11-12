'''
Travel Rule Messaging Protocols
https://notabene.id/travel-rule-messaging-protocols
IVMN101 : https://notabene.id/travel-rule-messaging-protocols/ivms-101#:~:text=What%20is%20IVMS%20101%3F,as%20their%20data%20transmission%20type.
OpenVASP : https://notabene.id/travel-rule-messaging-protocols/openvasp
TRP : https://notabene.id/travel-rule-messaging-protocols/trp

Travel Rule Implementation
HK : https://notabene.id/world/hong-kong
UK : https://notabene.id/world/united-kingdom
SG : https://notabene.id/world/singapore
'''

from flask import Flask, request, jsonify
import spacy

app = Flask(__name__)

# Load the pre-trained spaCy model
nlp = spacy.load("en_core_web_sm")


# Define a mapping of spaCy entity types to our custom categories
# NAME OF CUSTOMER / originator customer / beneficiary customer
# WALLET ADDRESS / wallet account / transaction number / account number
# CUSTOMER ID / customer identification number / unique identification number
# ID DOCUMENT NUMBER / national ID card / HKID / passport / DID
# ADDRESS OF CUSTOMER / residential address / business address
# DATE OF BIRTH / date of incorporation
# PLACE OF BIRTH / place of incorportation


def keyValueMatchingModel(key, value):
    # try to categorize based on key patterns
    key_lower = key.lower()
    
    # 1. Check for specific KEY patterns
    
    # Check if the JSON key is a single word and categorize accordingly
    if len(key.split()) == 1:  # Check if key is one word only
        if key_lower == "address":
            return "ADDRESS OF CUSTOMER"
        elif key_lower == "id":
            return "ID DOCUMENT NUMBER"
        elif key_lower == "customer":
            return "NAME OF CUSTOMER"
    
    # Check of Wallet Address
    if (
            (            
               any (word in key_lower for word in ["wallet"]) 
                    or
                    (
                   any (word in key_lower for word in ["crypto", "blockchain", "bitcoin", "ethereum", "transaction"]) 
                        and
                        any (word in key_lower for word in ["account", "address", "number"]) 
                    )
            or
            ("account" in key_lower and "number" in key_lower)
        )
        and 
        (      
            "key" not in key_lower and any (word not in key_lower for word in ["crypto", "public", "private"])
            )
        ): return "WALLET ADDRESS"
    
    # Check for Customer ID
    if (
        (
            "customer" in key_lower and any (word in key_lower for word in ["id", "identity", "identification"]) 
             or
             "unique" in key_lower and any (word in key_lower for word in ["id", "identity", "identification"])       
        )
        and  
        (      
            any (word not in key_lower for word in ["document", "national", "hkid", "passport", "did"])
            )
        ): return "CUSTOMER ID"
    
    # Check for ID document number
    if (
            (
            "document" in key_lower and any (word in key_lower for word in ["id", "identity", "identification"]) 
             or
             "national" in key_lower and any (word in key_lower for word in ["id", "identity", "identification"])       
             or
             any (word in key_lower for word in ["hkid", "passport", "did"]) 
        )  
        and  
        (      
            any (word not in key_lower for word in ["crypto", "blockchain"])
            )    
        ): return "ID DOCUMENT NUMBER"
    
    # Check for Date of Birth
    if (
            (
            any (word in key_lower for word in ["birthday"])
            or
                  (
                  any (word in key_lower for word in ["birth", "born"])
                  and  
                  any (word in key_lower for word in ["day", "date", "month", "year"])
              )
            )  
        and  
        (      
            any (word not in key_lower for word in ["place", "city", "country", "state"])
            )
        ): return "DATE OF BIRTH"
    
    # Check for Place of Birth
    if (
                 (
              any (word in key_lower for word in ["birth", "born"])
              and  
              any (word in key_lower for word in ["place", "city", "country", "state"])
          )  
        and  
        (      
            any (word not in key_lower for word in ["day", "date", "month", "year"])
            )
        ): return "PLACE OF BIRTH"

    # Check for Date of Incorporate
    if (
            (
            any (word in key_lower for word in ["incorporate", "company", "corporation"])
               and  
              any (word in key_lower for word in ["day", "date", "month", "year"])
          )
        and  
        (      
            any (word not in key_lower for word in ["place", "city", "country", "state"])
            )
        ): return "DATE OF INCORPORATE"
    
    # Check for Place of Incorporate
    if (
            (
            any (word in key_lower for word in ["incorporate", "company", "corporation"])
               and  
              any (word in key_lower for word in ["place", "city", "country", "state"])
          )  
        and  
        (      
            any (word not in key_lower for word in ["day", "date", "month", "year"])
            )
        ): return "PLACE OF INCORPORATE"

    # Check for Customer Name
    if (
            (
              any (word in key_lower for word in ["name", "surname", "middle name", "given name"])
              or
              (
                  any (word in key_lower for word in ["originator", "beneficiary"])
                  and 
                  any (word in key_lower for word in ["customer", "client", "user"])
              )
          )  
        and  
        (      
            any (word not in key_lower for word in ["id", "identity", "identification", "address"])
            )
        ): return "NAME OF CUSTOMER"
    
    # Check for Customer Address
    if (
            (
              any (word in key_lower for word in ["address"])
              and 
              any (word in key_lower for word in ["customer", "client", "user", "corresponding", "residential", "businesss", "company", "corporate", "incorporation"])
          )  
        and  
        (      
            any (word not in key_lower for word in ["wallet", "crypto", "blockchain", "bitcoin", "ethereum"])
            )
        ): return "ADDRESS OF CUSTOMER"
    
    # 2. Process the JSON value using spaCy for more complex cases
    
    #doc = nlp(f"{key}: {value}")
    doc = nlp(value)
    
    # Look for entities in both key and value
    for ent in doc.ents:
        # Directly check entity labels and map to custom categories
        label = ent.label_
        
        # Check for Date entities
        if label == "DATE":
            return "DATE_OF_BIRTH"
        
        # Check for Person entities
        elif label == "PERSON":
            return "NAME_OF_CUSTOMER"
        
        # Check for Address entities
        elif label in ["LOC"]:
            return "ADDRESS_OF_CUSTOMER"
        
        # Check for Geographic entities (GPE)
        elif label in ["GPE"]:
            return "PLACE_OF_BIRTH"
        
        # Handle special cases for CARDINAL type
        elif label == "CARDINAL":
            if is_wallet_address(value):
                return "WALLET_ADDRESS"
            elif is_address(value):
                return "ADDRESS_OF_CUSTOMER"    
            elif is_id_document(value):
                return "ID_DOCUMENT_NUMBER"    
            elif is_account_number(value):
                return "CUSTOMER_ACCOUNT"


        # 3. If no category found yet, try value-based heuristics
        if is_wallet_address(value):
                return "WALLET__ADDRESS"
        elif is_address(value):
                return "ADDRESS__OF__CUSTOMER"    
        elif is_date(value):
                return "DATE__OF__BIRTH"
        elif is_name(value) or is_PERSON_word(value):
                return "NAME__OF__CUSTOMER"

        # Default return if no category matched
        return None

def is_wallet_address(text):
    # Check if the text matches typical wallet address pattern
    #return text.startswith("0x") and len(text) >= 40
    #if text.startswith("0x") and len(text) >= 40:
    if text.startswith("0x") and len(text) == 42 and all(c in "0123456789abcdefABCDEF" for c in text[2:]):
    	return True
    if len(text) == 40 and all(c in "0123456789abcdefABCDEF" for c in text):
        return True
    # Check for Bitcoin address (P2PKH, P2SH, or bech32)
    # P2PKH (starts with '1'), P2SH (starts with '3'), or bech32 (starts with 'bc1')
    if (text.startswith('1') or text.startswith('3')) and len(text) >= 26 and len(text) <= 35:
        return True
    if text.startswith('bc1') and len(text) >= 42 and len(text) <= 62:  # Bech32 addresses
        return True
        
def is_id_document(text):
    # Check if the text matches typical ID document pattern (alphanumeric)
    return any(c.isalpha() for c in text) and any(c.isdigit() for c in text)
            
def is_account_number(text):
    # Check if the text is a numeric string
    return text.isdigit() and len(text) >= 9  #9 is an example

def is_name(text):
    # Check if text contains only letters and spaces
    #return all(c.isalpha() or c.isspace() for c in text)
    # List of common prefixes/titles to check for
    titles = ["mr", "mr.", "mrs", "mrs.", "ms", "ms.", "miss", "dr", "dr.", "prof", "prof."]    
    # Check if text contains only letters, spaces, and one of the specified titles
    words = text.lower().split()  # Convert text to lowercase and split into words
    if words[0] in titles:  # Check if the first word is a valid title
        return all(c.isalpha() or c.isspace() for c in text)  # Ensure all characters are letters or spaces
    return False  # If the first word is not a valid title, return False

def is_address(text):
    # Check if text contains common address elements
    #return "," in text and any(c.isdigit() for c in text)
    # List of common address elements to check for
    address_elements = ["st", "st.", "street", "flat", "rm", "room", "av.", "avenue", "rd.", "road"]
    # Check if text contains common address elements and any digits
    words = text.lower().split()  # Convert text to lowercase and split into words
    if any(element in words for element in address_elements) and any(c.isdigit() for c in text):
        return True
    return False
    
def is_date(text):
    # Check if text matches common date formats
    return any(x in text for x in [".", "/", "-"]) and any(c.isdigit() for c in text)
    
def is_2_words(text):
    # Split the text into words and check if there are exactly 2 words
    return len(text.split()) == 2
def is_3_words(text):
    # Split the text into words and check if there are exactly 3 words
    return len(text.split()) == 3
def is_PERSON_word(text):
    # Process the text with SpaCy to identify named entities
    docu = nlp(text)
    # Check if any entity in the text has the label "PERSON"
    for enty in docu.ents:
        if enty.label_ == "PERSON":
            return True
    return False
        

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
