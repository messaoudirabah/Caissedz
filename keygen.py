import hashlib

def generate_activation_code(hw_id):
    salt = "CAISSEDZ_SECRET_SALT_2026"
    combined = f"{hw_id}{salt}"
    activation_hash = hashlib.sha256(combined.encode()).hexdigest().upper()[:20]
    # Format: XXXXX-XXXXX-XXXXX-XXXXX
    return "-".join(activation_hash[i:i+5] for i in range(0, 20, 5))

if __name__ == "__main__":
    print("-" * 30)
    print("CAISSEDZ ACTIVATION GENERATOR")
    print("-" * 30)
    hwid = input("Enter Client Hardware ID: ").strip()
    if hwid:
        code = generate_activation_code(hwid)
        print(f"\nGenerated Activation Code: {code}")
        print("-" * 30)
    else:
        print("Invalid Hardware ID.")
