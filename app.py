from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify

from io import BytesIO

import base64, math, re, secrets, string



app = Flask(__name__)

ALPHABET = string.ascii_lowercase



def clean_letters(s):

    return ''.join(c.lower() for c in s if c.isalpha() and c.lower() in ALPHABET)



def group5(s):

    return ' '.join(s[i:i+5] for i in range(0, len(s), 5))



def validate_sub_key(key):

    k = clean_letters(key)

    if len(k) != 26 or len(set(k)) != 26:

        raise ValueError("Kunci substitusi harus tepat 26 huruf unik (a-z).")

    return k



def mod_inv(a, m):

    a %= m

    if math.gcd(a, m) != 1:

        raise ValueError(f"{a} tidak mempunyai invers modulo {m}.")

    return pow(a, -1, m)



def parse_affine(key, mod=26):

    parts = re.split(r'[\s,;]+', key.strip())

    if len(parts) != 2:

        raise ValueError("Kunci Affine harus berupa a,b. Contoh: 5,8")

    a, b = map(int, parts)

    mod_inv(a, mod)

    return a % mod, b % mod



def parse_perm(key):

    parts = re.split(r'[\s,;]+', key.strip())

    if not parts or any(not p.isdigit() for p in parts):

        raise ValueError("Kunci Permutation harus berupa urutan angka, contoh: 3 1 4 2")

    p = [int(x) for x in parts]

    if sorted(p) != list(range(1, len(p)+1)):

        raise ValueError("Permutation harus berisi semua angka 1..n tepat satu kali.")

    return [x-1 for x in p]



def parse_matrix(key):

    rows = [r.strip() for r in re.split(r'[;\n]+', key.strip()) if r.strip()]

    matrix = []

    for r in rows:

        vals = [int(x) for x in re.split(r'[\s,]+', r) if x]

        matrix.append(vals)

    if not matrix or any(len(r) != len(matrix) for r in matrix):

        raise ValueError("Matriks Hill harus persegi. Contoh 2x2: 3 3; 2 5")

    if len(matrix) not in (2,3):

        raise ValueError("Implementasi Hill text mendukung matriks 2x2 atau 3x3.")

    return matrix



def det2(M, mod):

    return (M[0][0]*M[1][1] - M[0][1]*M[1][0]) % mod



def det3(M, mod):

    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]

    return (a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)) % mod



def matrix_inv_mod(M, mod):

    n=len(M)

    if n==2:

        det=det2(M,mod)

        invdet=mod_inv(det,mod)

        return [[M[1][1]*invdet%mod, -M[0][1]*invdet%mod],

                [-M[1][0]*invdet%mod, M[0][0]*invdet%mod]]

    det=det3(M,mod)

    invdet=mod_inv(det,mod)

    a,b,c=M[0]; d,e,f=M[1]; g,h,i=M[2]

    cof=[

        [e*i-f*h, -(d*i-f*g), d*h-e*g],

        [-(b*i-c*h), a*i-c*g, -(a*h-b*g)],

        [b*f-c*e, -(a*f-c*d), a*e-b*d]

    ]

    adj=[list(x) for x in zip(*cof)]

    return [[x*invdet%mod for x in row] for row in adj]



def mat_vec(M, v, mod):

    return [sum(M[i][j]*v[j] for j in range(len(v))) % mod for i in range(len(M))]



def shift_text(s,k,decrypt=False):

    k=int(k)%26

    if decrypt: k=-k

    out=[]

    for c in s:

        if c.isalpha() and c.lower() in ALPHABET:

            base=ord('A') if c.isupper() else ord('a')

            out.append(chr((ord(c)-base+k)%26+base))

        else: out.append(c)

    return ''.join(out)



def substitution_text(s,key,decrypt=False):

    key=validate_sub_key(key)

    enc={ALPHABET[i]:key[i] for i in range(26)}

    if decrypt: enc={v:k for k,v in enc.items()}

    out=[]

    for c in s:

        lo=c.lower()

        if lo in enc:

            x=enc[lo]

            out.append(x.upper() if c.isupper() else x)

        else: out.append(c)

    return ''.join(out)



def affine_text(s,key,decrypt=False):

    a,b=parse_affine(key,26)

    if decrypt: a,b=mod_inv(a,26), (-mod_inv(a,26)*b)%26

    out=[]

    for c in s:

        lo=c.lower()

        if lo in ALPHABET:

            x=ord(lo)-97

            y=(a*x+b)%26

            out.append(chr(y+97).upper() if c.isupper() else chr(y+97))

        else: out.append(c)

    return ''.join(out)



def vigenere_text(s,key,decrypt=False):

    k=clean_letters(key)

    if not k: raise ValueError("Kunci Vigenere harus berisi huruf a-z.")

    ki=[ord(c)-97 for c in k]

    out=[]; j=0

    for c in s:

        if c.isalpha() and c.lower() in ALPHABET:

            x=ord(c.lower())-97

            y=(x + (-1 if decrypt else 1)*ki[j%len(ki)])%26

            out.append(chr(y+97))

            j+=1

    return ''.join(out)



def hill_text(s,key,decrypt=False):

    M=parse_matrix(key)

    if decrypt: M=matrix_inv_mod(M,26)

    letters=clean_letters(s)

    n=len(M)

    pad=(-len(letters))%n

    letters += 'x'*pad

    vals=[ord(c)-97 for c in letters]

    out=[]

    for i in range(0,len(vals),n):

        out.extend(mat_vec(M, vals[i:i+n],26))

    return ''.join(chr(x+97) for x in out)



def permutation_text(s,key,decrypt=False):

    p=parse_perm(key); n=len(p)

    letters=clean_letters(s)

    pad=(-len(letters))%n

    letters += 'x'*pad

    if decrypt:

        inv=[0]*n

        for i,pos in enumerate(p): inv[pos]=i

        order=inv

    else: order=p

    out=''

    for i in range(0,len(letters),n):

        block=letters[i:i+n]

        out += ''.join(block[j] for j in order)

    return out



def otp_text(s,key,decrypt=False):

    k=clean_letters(key)

    if not k: raise ValueError("Kunci OTP harus berisi huruf a-z.")

    letters=clean_letters(s)

    if len(k)<len(letters): raise ValueError("Kunci OTP lebih pendek dari jumlah huruf pesan.")

    out=[]

    for i,c in enumerate(letters):

        a=ord(c)-97; b=ord(k[i])-97

        out.append(chr((a-b if decrypt else a+b)%26+97))

    return ''.join(out)



def byte_sub_key(key):

    key=key.strip().replace(' ','')

    if not key:

        raw=bytes(range(256)); b=list(raw); secrets.SystemRandom().shuffle(b); return bytes(b)

    try: b=bytes.fromhex(key)

    except ValueError: raise ValueError("Kunci substitusi file harus HEX 512 karakter (256 byte).")

    if len(b)!=256 or len(set(b))!=256: raise ValueError("Kunci substitusi file harus tepat 256 byte unik.")

    return b



def parse_int_pair(key):

    parts=re.split(r'[\s,;]+',key.strip())

    if len(parts)!=2: raise ValueError("Kunci harus a,b.")

    return int(parts[0]),int(parts[1])



FILE_MAGIC = b"CRYPTOFILEv1\x00"


def _build_file_container(original_name, cipher, key_fingerprint, encrypted_data):
    name_bytes = original_name.encode("utf-8")
    cipher_bytes = cipher.encode("ascii")
    fp_bytes = key_fingerprint.encode("ascii")
    if len(name_bytes) > 65535 or len(cipher_bytes) > 255 or len(fp_bytes) > 255:
        raise ValueError("Metadata file terlalu panjang.")
    header = (FILE_MAGIC + len(name_bytes).to_bytes(4, "big") + bytes([len(cipher_bytes), len(fp_bytes)]) + name_bytes + cipher_bytes + fp_bytes)
    return header + encrypted_data


def _parse_file_container(raw):
    if not raw.startswith(FILE_MAGIC):
        raise ValueError("File bukan ciphertext CryptoLab (.enc) yang dibuat aplikasi.")
    pos = len(FILE_MAGIC)
    if len(raw) < pos + 6:
        raise ValueError("Header ciphertext rusak atau tidak lengkap.")
    name_len = int.from_bytes(raw[pos:pos+4], "big"); pos += 4
    cipher_len, fp_len = raw[pos], raw[pos+1]; pos += 2
    end = pos + name_len + cipher_len + fp_len
    if end > len(raw):
        raise ValueError("Metadata ciphertext tidak lengkap.")
    name = raw[pos:pos+name_len].decode("utf-8"); pos += name_len
    cipher = raw[pos:pos+cipher_len].decode("ascii"); pos += cipher_len
    fp = raw[pos:pos+fp_len].decode("ascii"); pos += fp_len
    return {"original_name": name, "cipher": cipher, "fingerprint": fp, "payload": raw[pos:]}


def _key_fingerprint(cipher, key):
    import hashlib
    if cipher == "substitution" and not key.strip():
        raise ValueError("Kunci Substitution File wajib diisi agar dekripsi memakai kunci yang sama.")
    return hashlib.sha256((cipher + "\x00" + key).encode("utf-8")).hexdigest()[:16]


def _inverse_matrix_2x2_mod256(M):
    a,b=M[0]; c,d=M[1]
    det=(a*d-b*c)%256
    if math.gcd(det,256)!=1:
        raise ValueError("Matriks Hill File tidak memiliki invers modulo 256. Gunakan determinan ganjil.")
    invdet=pow(det,-1,256)
    return [[d*invdet%256,-b*invdet%256],[-c*invdet%256,a*invdet%256]]


def _file_transform_raw(data,cipher,key,decrypt=False):
    data=bytes(data)
    if cipher=="shift":
        k=int(key)%256; k=-k if decrypt else k
        return bytes((x+k)%256 for x in data)
    if cipher=="substitution":
        k=byte_sub_key(key)
        if decrypt:
            inv=bytearray(256)
            for i,v in enumerate(k): inv[v]=i
            return bytes(inv[x] for x in data)
        return bytes(k[x] for x in data)
    if cipher=="affine":
        a,b=parse_int_pair(key); a%=256; b%=256
        if math.gcd(a,256)!=1:
            raise ValueError("Nilai a Affine File harus relatif prima dengan 256 (ganjil).")
        inv=pow(a,-1,256)
        return bytes(((x-b)*inv)%256 for x in data) if decrypt else bytes((a*x+b)%256 for x in data)
    if cipher=="vigenere":
        kb=key.encode("utf-8")
        if not kb: raise ValueError("Kunci Vigenere File tidak boleh kosong.")
        sign=-1 if decrypt else 1
        return bytes((x+sign*kb[i%len(kb)])%256 for i,x in enumerate(data))
    if cipher=="otp":
        kb=key.encode("utf-8")
        if len(kb)<len(data): raise ValueError("Kunci OTP File lebih pendek dari ukuran file.")
        sign=-1 if decrypt else 1
        return bytes((x+sign*kb[i])%256 for i,x in enumerate(data))
    if cipher=="hill":
        M=parse_matrix(key)
        if len(M)!=2: raise ValueError("Untuk Hill File gunakan matriks 2x2.")
        M=[[x%256 for x in row] for row in M]
        if decrypt:
            M=_inverse_matrix_2x2_mod256(M)
            if len(data)<4: raise ValueError("Ciphertext Hill File terlalu pendek.")
            original_len=int.from_bytes(data[:4],"big"); payload=data[4:]
            if len(payload)%2: raise ValueError("Payload Hill File rusak.")
            out=bytearray()
            for i in range(0,len(payload),2): out.extend(mat_vec(M,list(payload[i:i+2]),256))
            if original_len>len(out): raise ValueError("Panjang file asli tidak valid.")
            return bytes(out[:original_len])
        original_len=len(data); payload=data+(b"\x00" if len(data)%2 else b""); out=bytearray()
        for i in range(0,len(payload),2): out.extend(mat_vec(M,list(payload[i:i+2]),256))
        return original_len.to_bytes(4,"big")+bytes(out)
    if cipher=="permutation":
        p=parse_perm(key); n=len(p)
        if decrypt:
            if len(data)%n: raise ValueError("Ciphertext Permutation File rusak atau panjang blok tidak cocok.")
            inv=[0]*n
            for j,pos in enumerate(p): inv[pos]=j
            out=bytearray()
            for i in range(0,len(data),n):
                block=data[i:i+n]; out.extend(block[j] for j in inv)
            return bytes(out)
        if len(data)%n: raise ValueError(f"Ukuran file ({len(data)} byte) harus habis dibagi panjang permutation ({n}).")
        out=bytearray()
        for i in range(0,len(data),n):
            block=data[i:i+n]; out.extend(block[j] for j in p)
        return bytes(out)
    raise ValueError("Cipher tidak dikenali.")


def file_encrypt(raw,filename,cipher,key):
    encrypted=_file_transform_raw(raw,cipher,key,False)
    return _build_file_container(filename,cipher,_key_fingerprint(cipher,key),encrypted)


def file_decrypt(raw,cipher,key):
    meta=_parse_file_container(raw)
    if cipher and cipher!=meta["cipher"]:
        raise ValueError(f"Cipher tidak cocok. File dibuat dengan {meta['cipher'].title()}.")
    if _key_fingerprint(meta["cipher"],key)!=meta["fingerprint"]:
        raise ValueError("Kunci salah atau tidak sama dengan kunci saat enkripsi.")
    return meta["original_name"],_file_transform_raw(meta["payload"],meta["cipher"],key,True)

def text_encrypt(cipher,text,key):

    return {

        "shift": lambda:shift_text(text,key),

        "substitution": lambda:substitution_text(text,key),

        "affine": lambda:affine_text(text,key),

        "vigenere": lambda:vigenere_text(text,key),

        "hill": lambda:hill_text(text,key),

        "permutation": lambda:permutation_text(text,key),

        "otp": lambda:otp_text(text,key),

    }[cipher]()



def text_decrypt(cipher,text,key):

    return {

        "shift": lambda:shift_text(text,key,True),

        "substitution": lambda:substitution_text(text,key,True),

        "affine": lambda:affine_text(text,key,True),

        "vigenere": lambda:vigenere_text(text,key,True),

        "hill": lambda:hill_text(text,key,True),

        "permutation": lambda:permutation_text(text,key,True),

        "otp": lambda:otp_text(text,key,True),

    }[cipher]()



@app.route("/")

def index(): return render_template("index.html")



@app.post("/api/transform")
def transform():
    try:
        cipher=request.form.get("cipher","shift"); mode=request.form.get("mode","text")
        action=request.form.get("action","encrypt"); key=request.form.get("key","")
        if mode=="text":
            text=request.form.get("text","")
            result=text_encrypt(cipher,text,key) if action=="encrypt" else text_decrypt(cipher,text,key)
            return jsonify({"ok":True,"result":result,"grouped":group5(re.sub(r"[^a-zA-Z]","",result))})
        f=request.files.get("file")
        if not f: raise ValueError("Pilih file terlebih dahulu.")
        raw=f.read()
        if action=="encrypt":
            result=file_encrypt(raw,f.filename,cipher,key); filename=Path(f.filename).stem+".enc"
        else:
            original_name,result=file_decrypt(raw,cipher,key)
            filename=Path(original_name).stem+"_decrypted"+Path(original_name).suffix
        return jsonify({"ok":True,"filename":filename,"data":base64.b64encode(result).decode(),"size":len(result)})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}),400


@app.post("/api/otp-key")

def otp_key():

    n=max(1,int(request.form.get("length","10000")))

    n=min(n,1000000)

    key=''.join(secrets.choice(ALPHABET) for _ in range(n))

    return jsonify({"ok":True,"key":key,"length":n})



@app.post("/api/byte-sub-key")

def byte_sub_key_api():

    b=list(range(256)); secrets.SystemRandom().shuffle(b)

    return jsonify({"ok":True,"key":bytes(b).hex(),"length":256})



if __name__=="__main__":

    app.run(debug=True)




