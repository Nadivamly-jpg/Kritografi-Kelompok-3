# Perbaikan File CryptoLab

- Ciphertext file sekarang memakai container CRYPTOFILEv1.
- Nama file asli dan cipher disimpan di header ciphertext.
- Saat decrypt, ekstensi asli dipulihkan otomatis.
- Kunci diverifikasi dengan fingerprint SHA-256; kunci tidak disimpan di ciphertext.
- File dibaca/disimpan sebagai bytes.
- Hill File menangani ukuran file ganjil dengan metadata panjang asli.
- Substitution File wajib memakai key yang sama saat decrypt.
- Affine File memvalidasi gcd(a,256)=1.
- Permutation File menolak ukuran yang tidak habis dibagi panjang permutation agar tidak kehilangan byte.
