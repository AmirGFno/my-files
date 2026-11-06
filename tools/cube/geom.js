const fs=require('fs');
const src=fs.readFileSync(require('path').join(__dirname, '../../web/js/cube-engine.js'),'utf8');
const win={};
new Function('window','module','exports','requestAnimationFrame','cancelAnimationFrame','devicePixelRatio', src+'\nwindow.__x={Cube,CubeView,COLORS,VIEWS};')(win,{}, {},()=>{},()=>{},1);
const {CubeView,COLORS,VIEWS}=win.__x;

function makeCanvas(w,h,colourAware){
  const rec={polys:[]};
  let cur=[]; let fill='#000';
  const api={
    setTransform(){}, clearRect(){}, beginPath(){cur=[];},
    moveTo(x,y){cur.push([x,y]);}, lineTo(x,y){cur.push([x,y]);},
    quadraticCurveTo(x1,y1,x,y){cur.push([x,y]);},
    closePath(){ rec.polys.push({pts:cur.slice(), grad: api._lastGrad}); },
    _grad:null,
    createLinearGradient(){ const g={c:'#000', addColorStop(t,v){ if(!t) this.c=v; }}; api._lastGrad=g; return g; },
    fill(){ rec.gradFill=this; }, stroke(){}, ellipse(){},
    set fillStyle(v){fill=v;}, get fillStyle(){return fill;},
    set strokeStyle(v){}, set lineWidth(v){},
  };
  return {rec,width:0,height:0,style:{},getContext:()=>api,getBoundingClientRect:()=>({width:w,height:h}),addEventListener(){},setPointerCapture(){},clientWidth:w};
}
const hex=(c)=>'#'+c.map(q=>Math.round(Math.max(0,Math.min(1,q))*255).toString(16).padStart(2,'0')).join('');
const near=(h,rgb)=>{const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return Math.abs(r-rgb[0])<26&&Math.abs(g-rgb[1])<26&&Math.abs(b-rgb[2])<26;};
const faceOf=(hexColor)=>Object.entries(COLORS).find(([f,c])=>near(hexColor,c.map(q=>q*255)))?.[0];

function inside(pt,poly){
  let c=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++){
    const [xi,yi]=poly[i],[xj,yj]=poly[j];
    if(((yi>pt[1])!==(yj>pt[1])) && (pt[0] < (xj-xi)*(pt[1]-yi)/(yj-yi)+xi)) c=!c;
  }
  return c;
}

function analyse(viewName,W=420){
  const cv=makeCanvas(W,W);
  const v=new CubeView(cv,{view:viewName,interactive:false});
  v.resize(); cv.rec.polys.length=0; v.draw();
  const stickers=cv.rec.polys.slice(1);
  const area={}; let total=0;
  for(const s of stickers){
    let a=0; const p=s.pts;
    for(let i=0,j=p.length-1;i<p.length;j=i++) a+=(p[j][0]+p[i][0])*(p[j][1]-p[i][1]);
    a=Math.abs(a/2); total+=a;
    const col=(s.grad && s.grad.c) || '#000000';
    const key=faceOf(col) || 'x';
    area[key]=(area[key]||0)+a;
  }
  const pct={}; for(const k in area) pct[k]=+(100*area[k]/total).toFixed(1);
  // overlap test
  let maxHits=0;
  const pts=[];
  for(let i=0;i<60;i++) for(let j=0;j<60;j++) pts.push([W*(i+0.5)/60, W*(j+0.5)/60]);
  for(const pt of pts){
    let hits=0;
    for(const s of stickers) if(inside(pt,s.pts)) hits++;
    if(hits>maxHits) maxHits=hits;
  }
  return {count:stickers.length, pct, maxHits, total:Math.round(total)};
}

for(const name of Object.keys(VIEWS)){
  const r=analyse(name);
  console.log(name.padEnd(8), 'stickers', r.count, '| area%', JSON.stringify(r.pct), '| maxOverlap', r.maxHits);
}
