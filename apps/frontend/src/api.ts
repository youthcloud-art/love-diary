const base=(import.meta.env.VITE_API_BASE as string)||"http://127.0.0.1:8000";
export const token=()=>uni.getStorageSync("access_token") as string;
export const clear=()=>{uni.removeStorageSync("access_token");uni.removeStorageSync("refresh_token")};
export async function request<T>(url:string,method:"GET"|"POST"|"PATCH"|"DELETE"="GET",data?:any):Promise<T>{
 return new Promise((resolve,reject)=>uni.request({url:base+url,method,data,header:{Authorization:token()?`Bearer ${token()}`:""},success:r=>r.statusCode>=200&&r.statusCode<300?resolve(r.data as T):reject(new Error((r.data as any)?.detail||`请求失败 ${r.statusCode}`)),fail:e=>reject(new Error(e.errMsg))}));
}
export async function auth(path:string,data:any){const r=await request<any>(`/api/v1/auth/${path}`,"POST",data);uni.setStorageSync("access_token",r.access_token);uni.setStorageSync("refresh_token",r.refresh_token)}
export function upload(path:string):Promise<any>{return new Promise((resolve,reject)=>uni.uploadFile({url:base+"/api/v1/media",filePath:path,name:"file",header:{Authorization:`Bearer ${token()}`},success:r=>r.statusCode<300?resolve(JSON.parse(r.data)):reject(new Error(JSON.parse(r.data).detail)),fail:reject}))}

