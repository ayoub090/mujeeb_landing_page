export type Store = {id:string; name:string; platform:"salla"|"zid"|"shopify"|"custom"; currency:string; country_code:string};
export type User = {id:string; email:string; full_name:string; stores:Store[]};
export type Order = {id:string; external_order_number:string|null; amount:string; currency:string; status:string; risk_score:number; risk_level:"low"|"medium"|"high"; risk_reasons:Record<string,number>; created_at:string};
export type Summary = {total:number; confirmed:number; cancelled:number; human_follow_up:number; confirmation_rate:number};
