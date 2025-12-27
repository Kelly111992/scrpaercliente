"use client";

import { useState, useRef } from "react";

interface Lead {
  name: string;
  category: string;
  address: string;
  phone: string;
  website: string;
  rating: string;
  reviews_count: string;
  google_maps_url: string;
  ai_analysis: string;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [maxLeads, setMaxLeads] = useState(3);
  const [delayMin, setDelayMin] = useState(1000);
  const [delayMax, setDelayMax] = useState(3000);
  const [isScraping, setIsScraping] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [status, setStatus] = useState("Idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startScrape = async () => {
    setLeads([]);
    setIsScraping(true);
    setStatus("Starting...");

    try {
      const response = await fetch("http://localhost:8000/scrape/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          max_leads: maxLeads,
          delay_min_ms: delayMin,
          delay_max_ms: delayMax,
        }),
      });

      const data = await response.json();
      setJobId(data.job_id);
      connectSSE(data.job_id);
    } catch (error) {
      console.error("Error starting scrape:", error);
      setStatus("Error starting scrape. Is the backend running?");
      setIsScraping(false);
    }
  };

  const connectSSE = (id: string) => {
    if (eventSourceRef.current) eventSourceRef.current.close();

    const es = new EventSource(`http://localhost:8000/scrape/stream/${id}`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "status") {
        setStatus(data.message);
      } else if (data.type === "lead") {
        setLeads((prev) => [...prev, data.data]);
        setStatus(`Extracted ${data.count} leads...`);
      } else if (data.type === "done") {
        setStatus("Completed!");
        setIsScraping(false);
        es.close();
      } else if (data.type === "error") {
        setStatus(`Error: ${data.message}`);
        setIsScraping(false);
        es.close();
      }
    };

    es.onerror = (err) => {
      console.error("SSE error:", err);
    };
  };

  const downloadCSV = () => {
    if (jobId) {
      window.open(`http://localhost:8000/scrape/result/${jobId}.csv`);
    }
  };

  const downloadJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(leads));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "leads.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            G-Maps Lead Extractor
          </h1>
          <p className="text-slate-400 text-lg">Local tool for targeted business discovery</p>
        </header>

        <section className="bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-700 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-300">Google Maps Search URL</label>
              <input
                type="text"
                className="w-full p-3 bg-slate-950 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder:text-slate-600"
                placeholder="https://www.google.com/maps/search/dentist+near+mexico+city/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">Max Leads</label>
                <input
                  type="number"
                  className="w-full p-3 bg-slate-950 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  value={maxLeads}
                  onChange={(e) => setMaxLeads(parseInt(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">Min Delay (ms)</label>
                <input
                  type="number"
                  className="w-full p-3 bg-slate-950 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  value={delayMin}
                  onChange={(e) => setDelayMin(parseInt(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">Max Delay (ms)</label>
                <input
                  type="number"
                  className="w-full p-3 bg-slate-950 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  value={delayMax}
                  onChange={(e) => setDelayMax(parseInt(e.target.value))}
                />
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={startScrape}
                disabled={isScraping || !url}
                className={`px-8 py-3 rounded-lg font-bold transition-all shadow-lg active:scale-95 ${isScraping || !url
                  ? "bg-slate-700 cursor-not-allowed text-slate-400"
                  : "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/40"
                  }`}
              >
                {isScraping ? "Scraping..." : "Start Scraping"}
              </button>
              <div className="text-sm">
                <span className="text-slate-500">Status: </span>
                <span className="text-blue-400 font-medium">{status}</span>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={downloadCSV}
                disabled={leads.length === 0}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
              >
                CSV ⬇
              </button>
              <button
                onClick={downloadJSON}
                disabled={leads.length === 0}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
              >
                JSON ⬇
              </button>
            </div>
          </div>
        </section>

        <section className="bg-slate-800 rounded-2xl shadow-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto max-h-[600px]">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-900/50 sticky top-0 backdrop-blur-sm">
                <tr>
                  <th className="p-4 border-b border-slate-700 text-slate-400 font-semibold uppercase text-xs">Name</th>
                  <th className="p-4 border-b border-slate-700 text-slate-400 font-semibold uppercase text-xs">Category</th>
                  <th className="p-4 border-b border-slate-700 text-slate-400 font-semibold uppercase text-xs">Phone / Contact</th>
                  <th className="p-4 border-b border-slate-700 text-slate-400 font-semibold uppercase text-xs">Website</th>
                  <th className="p-4 border-b border-slate-700 text-slate-400 font-semibold uppercase text-xs">Rating</th>
                  <th className="p-4 border-b border-slate-700 text-slate-400 font-semibold uppercase text-xs w-1/3">AI Analysis / Opportunities</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {leads.map((lead, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors animate-in fade-in slide-in-from-left-2 duration-300">
                    <td className="p-4 font-medium">{lead.name}</td>
                    <td className="p-4 text-slate-400">{lead.category}</td>
                    <td className="p-4">
                      <div className="flex flex-col space-y-2">
                        <span className="text-emerald-400 font-mono text-sm">{lead.phone || "-"}</span>
                        {lead.phone && (
                          <button
                            onClick={() => {
                              // Clean phone number (keep only digits)
                              const cleanPhone = lead.phone.replace(/\D/g, '');
                              // Use the full message/speech template
                              const message = lead.ai_analysis;
                              const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;
                              window.open(url, '_blank');
                            }}
                            className="flex items-center space-x-1 text-[10px] bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 px-2 py-1 rounded border border-emerald-600/30 transition-all w-fit"
                          >
                            <span>WhatsApp</span>
                            <span className="text-xs">↗</span>
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      {lead.website ? (
                        <a href={lead.website} target="_blank" className="text-blue-400 hover:text-blue-300 hover:underline truncate block max-w-[200px]">
                          {lead.website}
                        </a>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-1">
                        <span className="text-yellow-400">★</span>
                        <span className="font-medium">{lead.rating || "N/A"}</span>
                        <span className="text-slate-500 text-xs">({lead.reviews_count || 0})</span>
                      </div>
                    </td>
                    <td className="p-4 text-xs">
                      <div className="bg-slate-900/50 p-3 rounded border border-slate-700 text-slate-300 leading-relaxed whitespace-pre-wrap">
                        {lead.ai_analysis}
                      </div>
                    </td>
                  </tr>
                ))}
                {leads.length === 0 && !isScraping && (
                  <tr>
                    <td colSpan={5} className="p-12 text-center text-slate-500">
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-4xl text-slate-600">🔍</span>
                        <p>No leads extracted yet. Paste a Google Maps URL above to start.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
