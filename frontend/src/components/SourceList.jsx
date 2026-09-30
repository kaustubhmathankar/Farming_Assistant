import { ExternalLink, FileText, Globe2, Landmark, CloudSun } from "lucide-react";

const icons = { government: Landmark, weather: CloudSun, market: Landmark, knowledge: FileText, web: Globe2 };

export default function SourceList({ sources = [] }) {
  if (!sources.length) return null;
  return <div className="sources"><div className="sources-title">Sources used</div><div className="source-grid">{sources.map((s, i) => { const Icon = icons[s.type] || Globe2; return <a className="source-card" key={`${s.url || s.title}-${i}`} href={s.url || "#"} target={s.url ? "_blank" : undefined} rel="noreferrer"><span className="source-icon"><Icon size={16} /></span><span className="source-copy"><strong>{s.title || "Source"}</strong><small>{s.source || s.type}</small></span>{s.url && <ExternalLink size={14} />}</a>; })}</div></div>;
}
