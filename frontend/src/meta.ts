declare global { interface Window { FB?: {init:(config:object)=>void; login:(callback:(response:{authResponse?:{code?:string}})=>void, options:object)=>void}; fbAsyncInit?:()=>void; } }

export function loadMetaSdk(appId:string) {
  return new Promise<void>((resolve, reject) => {
    if (window.FB) return resolve();
    window.fbAsyncInit = () => { window.FB!.init({appId, cookie:true, xfbml:true, version: import.meta.env.VITE_META_GRAPH_VERSION || "v23.0"}); resolve(); };
    const script = document.createElement("script"); script.src = "https://connect.facebook.net/en_US/sdk.js"; script.async = true; script.onerror = () => reject(new Error("Meta SDK failed to load")); document.body.appendChild(script);
  });
}

type SignupResult = {code:string; waba_id:string; phone_number_id:string};

export async function launchEmbeddedSignup():Promise<SignupResult> {
  if (import.meta.env.VITE_META_EMBEDDED_SIGNUP_ENABLED !== "true") throw new Error("Embedded Signup is awaiting Meta approval");
  await loadMetaSdk(import.meta.env.VITE_META_APP_ID);
  return new Promise((resolve, reject) => {
    let code=""; let waba_id=""; let phone_number_id="";
    const finish=()=>{if(code&&waba_id&&phone_number_id){cleanup();resolve({code,waba_id,phone_number_id});}};
    const listener=(event:MessageEvent)=>{
      if (!new Set(["https://www.facebook.com","https://web.facebook.com"]).has(event.origin)) return;
      let data=event.data; try{if(typeof data==="string")data=JSON.parse(data);}catch{return;}
      if(data?.type==="WA_EMBEDDED_SIGNUP"&&data?.event==="FINISH"){
        waba_id=String(data.data?.waba_id||""); phone_number_id=String(data.data?.phone_number_id||""); finish();
      }
    };
    const timer=window.setTimeout(()=>{cleanup();reject(new Error("انتهت مهلة ربط واتساب"));},120000);
    const cleanup=()=>{window.clearTimeout(timer);window.removeEventListener("message",listener);};
    window.addEventListener("message",listener);
    window.FB!.login(response=>{if(response.authResponse?.code){code=response.authResponse.code;finish();}else{cleanup();reject(new Error("WhatsApp authorization was cancelled"));}}, {
      config_id: import.meta.env.VITE_META_CONFIG_ID, response_type:"code", override_default_response_type:true,
      extras:{feature:"whatsapp_embedded_signup", sessionInfoVersion:"3"}
    });
  });
}
