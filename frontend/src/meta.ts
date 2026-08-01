declare global { interface Window { FB?: {init:(config:object)=>void; login:(callback:(response:{authResponse?:{code?:string}})=>void, options:object)=>void}; fbAsyncInit?:()=>void; } }

export function loadMetaSdk(appId:string) {
  return new Promise<void>((resolve, reject) => {
    if (window.FB) return resolve();
    window.fbAsyncInit = () => { window.FB!.init({appId, cookie:true, xfbml:true, version: import.meta.env.VITE_META_GRAPH_VERSION || "v23.0"}); resolve(); };
    const script = document.createElement("script"); script.src = "https://connect.facebook.net/en_US/sdk.js"; script.async = true; script.onerror = () => reject(new Error("Meta SDK failed to load")); document.body.appendChild(script);
  });
}

export async function launchEmbeddedSignup():Promise<string> {
  await loadMetaSdk(import.meta.env.VITE_META_APP_ID);
  return new Promise((resolve, reject) => window.FB!.login(response => response.authResponse?.code ? resolve(response.authResponse.code) : reject(new Error("WhatsApp authorization was cancelled")), {
    config_id: import.meta.env.VITE_META_CONFIG_ID, response_type:"code", override_default_response_type:true,
    extras:{feature:"whatsapp_embedded_signup", sessionInfoVersion:"3"}
  }));
}
