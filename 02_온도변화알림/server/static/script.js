const $=id=>document.getElementById(id);
const names={WARMING_UP:"측정 준비",STABLE:"정상",RISING:"상승 경보",FALLING:"하강 경보",SENSOR_ERROR:"센서 오류"};
const fmt=v=>typeof v==="number"?v.toFixed(1)+" °C":"--";
const timeText=v=>new Date(v).toLocaleString("ko-KR");
const color=s=>s==="RISING"?"rise":s==="FALLING"?"fall":s==="SENSOR_ERROR"?"error":"";
function node(tag,attrs,text){const n=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
function draw(rows){
  const svg=$("graph");svg.replaceChildren();
  const valid=rows.filter(r=>typeof r.temperature==="number");
  if(!valid.length){$("graphInfo").textContent="표시할 온도 기록이 없습니다.";return;}
  const min=Math.min(...valid.map(r=>r.temperature))-1,max=Math.max(...valid.map(r=>r.temperature))+1;
  const start=Date.parse(rows[0].received_at),end=Date.parse(rows.at(-1).received_at);
  const x=r=>end===start?350:55+600*(Date.parse(r.received_at)-start)/(end-start);
  const y=v=>195-170*(v-min)/(max-min);
  for(let i=0;i<=4;i++){const v=min+(max-min)*i/4;svg.append(node("line",{x1:55,x2:655,y1:y(v),y2:y(v),stroke:"#dce4ec"}),node("text",{x:5,y:y(v)+4,fill:"#475569","font-size":12},v.toFixed(1)));}
  let prev=null;
  for(const r of rows){if(r.temperature===null){prev=null;continue;}
    if(prev&&r.boot===prev.boot&&r.seq===prev.seq+1&&Date.parse(r.received_at)-Date.parse(prev.received_at)<10000)svg.append(node("line",{x1:x(prev),y1:y(prev.temperature),x2:x(r),y2:y(r.temperature),stroke:"#2563eb","stroke-width":2}));
    svg.append(node("circle",{cx:x(r),cy:y(r.temperature),r:r.alarm?4:2,fill:r.alarm?(r.state==="RISING"?"#b91c1c":"#1d4ed8"):"#2563eb"}));prev=r;}
  $("graphInfo").textContent=timeText(rows[0].received_at)+" ~ "+timeText(rows.at(-1).received_at);
}
let version=0;
async function update(){
  const v=++version, query=$("day").value?"?date="+encodeURIComponent($("day").value):"";
  $("csv").href="/api/export.csv"+query;
  try{
    const response=await fetch("/api/status"+query,{cache:"no-store",signal:AbortSignal.timeout(4000)});
    if(!response.ok)throw Error("HTTP");
    const d=await response.json();if(v!==version)return;
    const r=d.latest;
    $("connection").textContent=d.live?"실시간 수신 중":d.connected?"USB 연결됨 · 새 측정 대기":"수신 중단 · 저장 기록 조회";
    $("temp").textContent=fmt(d.live?r?.temperature:null);
    $("delta").textContent=fmt(d.live?r?.delta:null);
    $("state").textContent=d.live?(names[r?.state]||"--"):"실시간 수신 없음";
    $("state").className=d.live?color(r?.state):"error";
    for(const [id,key] of [["max","maximum"],["min","minimum"],["avg","average"]])$(id).textContent=fmt(d.stats[key]);
    $("count").textContent=d.stats.alarms;
    draw(d.history);$("alarms").replaceChildren();
    for(const row of d.alarms){const tr=document.createElement("tr");for(const val of [timeText(row.received_at),fmt(row.temperature),fmt(row.delta),names[row.state]]){const td=document.createElement("td");td.textContent=val;tr.append(td);}$("alarms").append(tr);}
  }catch(err){if(v===version){$("connection").textContent="서버 연결 실패";$("temp").textContent="--";$("delta").textContent="--";$("state").textContent="연결 오류";$("state").className="error";}}
}
$("day").addEventListener("change",update);$("all").addEventListener("click",()=>{$("day").value="";update();});
update();setInterval(update,3000);
