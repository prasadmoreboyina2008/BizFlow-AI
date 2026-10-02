const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export function setToken(token){ token ? localStorage.setItem('bizflow-token',token) : localStorage.removeItem('bizflow-token') }
export function hasToken(){ return Boolean(localStorage.getItem('bizflow-token')) }
export async function api(path, options={}){
  const headers={...(options.body?{'Content-Type':'application/json'}:{}), ...(localStorage.getItem('bizflow-token')?{Authorization:`Bearer ${localStorage.getItem('bizflow-token')}`}:{ }), ...options.headers}
  const response=await fetch(`${BASE}/api${path}`,{...options,headers})
  if(!response.ok){let message=`Request failed (${response.status})`;try{const data=await response.json();message=data.detail||message}catch{};throw new Error(message)}
  if(response.status===204)return null
  return response.json()
}
