#!/usr/bin/env node
/**
 * A461 CPU reanalysis of archived kev-4B K-C four typed readouts.
 * Usage: node A461_kc_fourhead_cpu_v1.js RAW_JSONL DESIGN_JSON [ROSTER_JSON|-] [OUT_JSON]
 * Default roster source is pinned Git blob in current cloned repository. No GPU.
 */
function auditFourHead(rawText,designText,rosterText) {
  const rows=rawText.trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
  const design=JSON.parse(designText),roster=JSON.parse(rosterText);
  if(rows.length!==417)throw Error("Expected frozen 417 K-C rows");
  const seen=new Set(rows.map(r=>r.forward_index));
  if(seen.size!==417||[...seen].sort((a,b)=>a-b).some((v,i)=>v!==i+1))throw Error("Forward bijection");
  const donors=new Map(design.selection.replication_donors.map(([id,g])=>[id,g]));
  const hosts=new Map(design.selection.replication_hosts.map(([id,g])=>[id,g]));
  const oracle=new Map(roster.candidates.map(r=>[r.scene_sha256,r.oracle_new]));
  const pairs=new Map(),cnt={};
  for(const r of rows) {
    cnt[r.condition]=(cnt[r.condition]||0)+1;
    if(!/^patch_kc_(main|sasham|doserand)_all$/.test(r.condition))continue;
    const key=r.donor+"|"+r.host, p=pairs.get(key)||{};
    if(p[r.condition])throw Error("Repeated pair arm");
    p[r.condition]=r;pairs.set(key,p);
  }
  const q=(r,id)=>{const x=r.questions.find(q=>q.id===id);if(!x||x.logits.length!==x.keys.length)throw Error("Bad native q "+id);return x};
  const arg=(r,id)=>{const x=q(r,id);return x.keys[x.logits.indexOf(Math.max(...x.logits))]};
  const j=r=>arg(r,"conflicting_vote")==="true"&&arg(r,"certificate_action")==="reject_conflict";
  const meanOrdinal=(r,T)=>{const v=q(r,"evidence_level"),m=Math.max(...v.logits);const w=v.logits.map(a=>Math.exp((a-m)/T)),s=w.reduce((a,b)=>a+b,0);return w.reduce((a,b,i)=>a+Number(v.keys[i])*b,0)/s};
  const median=(a)=>{const b=[...a].sort((x,y)=>x-y),k=b.length;return(b[(k-1)>>1]+b[k>>1])/2};
  const outcomes={valid_cross_group:0,same_group_excluded:0,host_gold_verified:0,main_joint:0,sham_joint:0,dose_joint:0,main_e_argmax_2:0,e_argmax_changes_vs_sham:0,e_argmax_0_to_2:0,e_argmax_1_to_2:0,q_changes_vs_sham:0,q_wrong_gold_main:0,q_wrong_gold_sham:0,q_wrong_in_joint:0,e_argmax_2_in_joint:0,temperature:{},by_host:{}};
  const temps=[0.5,1,2.41,5],diffs=Object.fromEntries(temps.map(T=>[T,{sham:[],dose:[],joint:[],nonjoint:[],byDonor:new Map()}]));
  for(const [k,p]of pairs){
    const [d,h]=k.split("|");
    if(!donors.has(d)||!hosts.has(h))throw Error("Unfrozen donor or host");
    if(donors.get(d)===hosts.get(h)){outcomes.same_group_excluded++;continue;}
    const m=p.patch_kc_main_all,s=p.patch_kc_sasham_all,z=p.patch_kc_doserand_all;
    if(!m||!s||!z)throw Error("Missing arm: "+k);
    const gold=oracle.get(h);if(!gold||gold.conflicting_vote!==true||gold.certificate_action!=="reject_conflict")throw Error("Invalid oracle");
    outcomes.host_gold_verified++;outcomes.valid_cross_group++;
    const mj=j(m);outcomes.main_joint+=+mj;outcomes.sham_joint+=+j(s);outcomes.dose_joint+=+j(z);
    const e0=arg(s,"evidence_level"),e1=arg(m,"evidence_level");
    outcomes.main_e_argmax_2+=+(e1==="2");outcomes.e_argmax_2_in_joint+=+(mj&&e1==="2");
    outcomes.e_argmax_changes_vs_sham+=+(e0!==e1);
    outcomes.e_argmax_0_to_2+=+(e0==="0"&&e1==="2");
    outcomes.e_argmax_1_to_2+=+(e0==="1"&&e1==="2");
    outcomes.q_changes_vs_sham+=+(arg(m,"quorum")!==arg(s,"quorum"));
    outcomes.q_wrong_gold_main+=+(arg(m,"quorum")!==String(gold.quorum));
    outcomes.q_wrong_gold_sham+=+(arg(s,"quorum")!==String(gold.quorum));
    outcomes.q_wrong_in_joint+=+(mj&&arg(m,"quorum")!==String(gold.quorum));
    const bh=outcomes.by_host[h]||(outcomes.by_host[h]={source_group:hosts.get(h),gold_quorum:gold.quorum,matched_cells:0,joint_repairs:0,delta_e_t1:[],quorum_correct:arg(s,"quorum")===String(gold.quorum)});
    bh.matched_cells++;bh.joint_repairs+=+mj;
    for(const T of temps){
      const dt=diffs[T],ds=meanOrdinal(m,T)-meanOrdinal(s,T),dd=meanOrdinal(m,T)-meanOrdinal(z,T);
      dt.sham.push(ds);dt.dose.push(dd);
      (mj?dt.joint:dt.nonjoint).push(ds);
      if(T===1)bh.delta_e_t1.push(ds);
      let arr=dt.byDonor.get(donors.get(d))||[];arr.push(ds);dt.byDonor.set(donors.get(d),arr);
    }
  }
  if(outcomes.valid_cross_group!==104||outcomes.same_group_excluded!==8)throw Error("Cross-group scope changed");
  for(const T of temps){
    const x=diffs[T];
    outcomes.temperature[String(T)]={positive_vs_sham:x.sham.filter(v=>v>1e-9).length,positive_vs_dose:x.dose.filter(v=>v>1e-9).length,median_delta_vs_sham:+median(x.sham).toFixed(6),median_delta_vs_dose:+median(x.dose).toFixed(6),source_groups_with_positive_sham:x.byDonor.size,joint_positive:x.joint.filter(v=>v>1e-9).length,nonjoint_positive:x.nonjoint.filter(v=>v>1e-9).length};
  }
  for(const v of Object.values(outcomes.by_host)){v.median_delta_e_t1=+median(v.delta_e_t1).toFixed(6);delete v.delta_e_t1}
  const expect={main_joint:53,sham_joint:0,dose_joint:0,main_e_argmax_2:24,q_changes_vs_sham:0,q_wrong_in_joint:6};
  for(const [k,v] of Object.entries(expect))if(outcomes[k]!==v)throw Error("Unexpected frozen result "+k+": "+outcomes[k]);
  if(outcomes.temperature["1"].positive_vs_sham!==103||outcomes.temperature["1"].positive_vs_dose!==99)throw Error("Unexpected E signed effects");
  return {schema:"JEV_A461_POSTPASS_FOURHEAD_CPU_REANALYSIS_V1",data_status:"CPU_REANALYSIS_ONLY_NO_GPU",source:{raw_blob:"19d3a06c27953b1f2b4dcd2770394d28741a69fd",roster_blob:"1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8",design_blob:"cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f"},conditions:cnt,summary:outcomes,limitations:["E is an ordinal score; argmax=2 is an exploratory diagnostic, not native calibrated score correctness","E_T uses logit-softmax weighted 0/1/2 with a selected T and is not certified as the official inference scorer","104 cells reuse donors and hosts; no IID significance claims","Q Gold read from independently frozen oracle_new in candidate roster; new arm has C=true, A=reject_conflict"]};
}
const fs=require('node:fs');
const cp=require('node:child_process');
if(require.main===module){
  const [rawPath,designPath,rosterPath,outPath]=process.argv.slice(2);
  if(!rawPath||!designPath){console.error('Usage: node A461_kc_fourhead_cpu_v1.js RAW_JSONL DESIGN_JSON [ROSTER_JSON|-] [OUT_JSON]');process.exit(2);}
  const txt=p=>fs.readFileSync(p,'utf8');
  const r=rosterPath&&rosterPath!=='-'?txt(rosterPath):cp.execFileSync('git',['cat-file','blob','1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8'],{encoding:'utf8'});
  const result=auditFourHead(txt(rawPath),txt(designPath),r),out=JSON.stringify(result,null,2)+'\n';
  if(outPath)fs.writeFileSync(outPath,out);
  process.stdout.write(out);
}
module.exports={auditFourHead};
