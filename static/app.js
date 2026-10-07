const state={cipher:"shift",mode:"text",lastFile:null,lastDownload:null};
const meta={
shift:["Shift Cipher","Setiap huruf digeser sejumlah posisi pada alfabet 26 huruf.","C = (P + k) mod 26","Angka k, contoh: 3"],
substitution:["Substitution Cipher","Setiap huruf dipetakan ke huruf lain berdasarkan alfabet kunci.","C = S(P)","26 huruf unik, contoh: qwertyuiopasdfghjklzxcvbnm"],
affine:["Affine Cipher","Transformasi linear dengan pasangan kunci a,b.","C = (aP + b) mod 26","a,b; contoh: 5,8"],
vigenere:["Vigenere Cipher","Pergeseran setiap huruf menggunakan kunci yang berulang.","C = (P + K) mod 26","Kata kunci, contoh: kripto"],
hill:["Hill Cipher","Enkripsi blok menggunakan matriks 2x2 atau 3x3.","C = KP mod 26","2x2: 3 3; 2 5"],
permutation:["Permutation Cipher","Huruf disusun ulang berdasarkan urutan posisi dalam blok.","C = permute(P)","Contoh: 3 1 4 2"],
otp:["One-time Pad","Setiap huruf memakai satu huruf kunci acak yang tidak diulang.","C = (P + K) mod 26","Kunci huruf a-z; bisa generate 10.000 huruf"]
};
function $(id){return document.getElementById(id)}
function render(){
  document.querySelectorAll(".cipher").forEach(x=>x.classList.toggle("active",x.dataset.cipher===state.cipher));
  document.querySelectorAll(".mode").forEach(x=>x.classList.toggle("active",x.dataset.mode===state.mode));
  const m=meta[state.cipher]; $("info-title").textContent=m[0];$("info-desc").textContent=m[1];$("formula").textContent=m[2];$("keyhint").textContent="— "+m[3];
  $("filebox").hidden=state.mode!=="file"; $("text").parentElement.hidden=state.mode==="file";
  $("otp-tools").hidden=!(state.cipher==="otp"||state.cipher==="substitution");
  $("text").placeholder=state.mode==="text"?"Ketik pesan yang ingin dienkripsi...":"";
}
document.querySelectorAll(".cipher").forEach(b=>b.onclick=()=>{state.cipher=b.dataset.cipher;render()});
document.querySelectorAll(".mode").forEach(b=>b.onclick=()=>{state.mode=b.dataset.mode;render()});
$("file").onchange=e=>state.lastFile=e.target.files[0];
async function run(action){
  const fd=new FormData();fd.append("cipher",state.cipher);fd.append("mode",state.mode);fd.append("action",action);fd.append("key",$("key").value);
  if(state.mode==="text") fd.append("text",$("text").value);
  else {if(!state.lastFile)return alert("Pilih file terlebih dahulu.");fd.append("file",state.lastFile)}
  $("status").textContent="Memproses...";
  try{
    const r=await fetch("/api/transform",{method:"POST",body:fd}), d=await r.json();
    if(!r.ok||!d.ok) throw new Error(d.error||"Gagal memproses");
    if(state.mode==="text"){ $("result").value=d.result; $("count").textContent=d.result.length+" karakter"; state.lastDownload=null}
    else { const bytes=Uint8Array.from(atob(d.data),c=>c.charCodeAt(0));state.lastDownload={name:d.filename,bytes};$("result").value="File berhasil diproses.\n\n"+d.filename+"\nUkuran: "+d.size+" byte";$("count").textContent=d.size+" byte" }
    $("status").textContent=action==="encrypt"?"Enkripsi selesai":"Dekripsi selesai";
  }catch(e){$("status").textContent="Terjadi kesalahan";alert(e.message)}
}
$("encrypt").onclick=()=>run("encrypt");$("decrypt").onclick=()=>run("decrypt");
$("copy").onclick=async()=>{await navigator.clipboard.writeText($("result").value);$("status").textContent="Hasil disalin"};
$("download").onclick=()=>{
 if(state.mode==="file"&&state.lastDownload){const b=new Blob([state.lastDownload.bytes]);const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=state.lastDownload.name;a.click();return}
 const blob=new Blob([$("result").value],{type:"text/plain"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="ciphertext.txt";a.click()
};
$("genotp").onclick=async()=>{const fd=new FormData();fd.append("length","10000");const d=await (await fetch("/api/otp-key",{method:"POST",body:fd})).json();$("key").value=d.key;alert("OTP 10.000 huruf berhasil dibuat.")};
$("gensub").onclick=async()=>{const d=await (await fetch("/api/byte-sub-key",{method:"POST"})).json();$("key").value=d.key;state.mode="file";render();alert("Byte substitution key 256 byte berhasil dibuat dan mode File dipilih.")};
render();
