import React, { useState, useEffect } from 'react';
import { Cpu, Shield, Activity, RefreshCw, Layers, Zap, CheckCircle2, AlertCircle, Database, Eye } from 'lucide-react';
import { useLanguage } from '../services/LanguageContext';

export default function AgentStatusPanel() {
  const { t, lang } = useLanguage();
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const fetchAgentStatus = async () => {
    try {
      const resp = await fetch('http://localhost:8000/api/v1/agents/status');
      if (resp.ok) {
        const data = await resp.json();
        setStatusData(data);
      }
    } catch (err) {
      console.error("Agent status fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentStatus();
    const interval = setInterval(fetchAgentStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleManualTrigger = async (platform = "x") => {
    setTriggering(true);
    try {
      await fetch(`http://localhost:8000/api/v1/agents/trigger_crawl?platform=${platform}`, {
        method: 'POST'
      });
      await fetchAgentStatus();
    } catch (err) {
      console.error("Crawl trigger error:", err);
    } finally {
      setTriggering(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'RUNNING') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-300 animate-pulse">
          <Activity className="w-3.5 h-3.5 animate-spin" /> ACTIVE RUN
        </span>
      );
    }
    if (status === 'ERROR') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-300">
          <AlertCircle className="w-3.5 h-3.5" /> ERROR
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
        <CheckCircle2 className="w-3.5 h-3.5" /> ONLINE / READY
      </span>
    );
  };

  const agentNames = {
    crawler_agent: { label: lang === 'hi' ? 'क्रॉलर और स्क्रैपर एजेंट' : lang === 'gu' ? 'ક્રોલીંગ અને સ્ક્રેપર એજન્ટ' : 'Multi-Platform Crawler Agent', icon: Layers, desc: 'X, Instagram, Facebook & YouTube Ingestion' },
    nlp_classifier_agent: { label: lang === 'hi' ? 'एनएलपी व थ्रेट क्लासिफायर' : lang === 'gu' ? 'NLP અને ખતરા વર્ગીકરણ' : 'NLP Threat Classifier Agent', icon: Cpu, desc: 'OpenRouter Multi-Agent & Language Detection' },
    network_agent: { label: lang === 'hi' ? 'नेटवर्क व बॉट विश्लेषक' : lang === 'gu' ? 'નેટવર્ક અને બોટ વિશ્લેષક' : 'Graph & Network Analyst', icon: Shield, desc: 'Bot Cluster & Amplification Mapping' },
    alert_agent: { label: lang === 'hi' ? 'अलर्ट एवं एस्केलेशन इंजन' : lang === 'gu' ? 'એલર્ટ અને એસ્કેલેશન એન્જિન' : 'Alert & Escalation Engine', icon: Zap, desc: 'Threshold Evaluation & Police Dispatch' },
    learning_agent: { label: lang === 'hi' ? 'लर्निंग व रिट्रेनिंग एजेंट' : lang === 'gu' ? 'લર્નિંગ અને રીટ્રેનિંગ એજન્ટ' : 'Human-in-the-Loop Learner', icon: Database, desc: 'Duty Officer Feedback & Model Retraining' },
    report_agent: { label: lang === 'hi' ? 'सरकारी रिपोर्ट जनरेटर' : lang === 'gu' ? 'સરકારી રિપોર્ટ જનરેટર' : 'CTI Report Generator Agent', icon: Eye, desc: 'AI Incident Brief Synthesis' },
  };

  return (
    <div className="bg-white rounded-xl shadow-md border-2 border-indigo-100 overflow-hidden mb-8 transition-all hover:shadow-lg">
      <div className="bg-gradient-to-r from-indigo-900 via-blue-900 to-indigo-950 px-6 py-4 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-400/30">
            <Cpu className="w-6 h-6 text-indigo-300 animate-pulse" />
          </div>
          <div>
            <h3 className="font-bold text-lg leading-tight">
              {lang === 'hi' ? 'हर्मिस (Hermes) स्वायत्त एआई मल्टी-एजेंट नियंत्रण कक्ष' : lang === 'gu' ? 'હર્મીસ (Hermes) ઓટોનોમસ AI મલ્ટી-એજન્ટ કંટ્રોલ રૂમ' : 'Hermes Autonomous AI Multi-Agent Control Room'}
            </h3>
            <p className="text-xs text-indigo-200 mt-0.5">
              {lang === 'hi' ? 'ओपनराउटर व हर्मिस आर्किटेक्चर द्वारा 6 स्वायत्त एजेंटों का लाइव समन्वय (ERH26_PS_05)' : lang === 'gu' ? 'OpenRouter અને Hermes દ્વારા 6 સ્વાયત્ત એજન્ટોનું રીયલ-ટાઇમ સંકલન' : 'Live Orchestration of 6 Autonomous CTI Agents via OpenRouter & Hermes Architecture'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleManualTrigger('x')}
            disabled={triggering}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            title="Harvest new sample from X (Twitter)"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${triggering ? 'animate-spin' : ''}`} />
            {lang === 'hi' ? 'लाइव क्रॉल चलाएं' : 'Trigger Live Crawl'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-gray-500 flex items-center justify-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
          <span>{lang === 'hi' ? 'एजेंट स्थिति डेटा लोड किया जा रहा है...' : 'Loading Hermes Agent telemetry...'}</span>
        </div>
      ) : statusData && statusData.agents ? (
        <div className="p-5 bg-gray-50/60">
          {/* Pipeline stages summary bar */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2 mb-5">
            {statusData.pipeline_stages?.map((s, idx) => (
              <div key={idx} className="bg-white p-2.5 rounded-lg border border-gray-200/80 shadow-xs text-center">
                <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider block">{s.stage}</span>
                <span className="text-xs font-semibold text-gray-800 mt-0.5 block truncate">{s.agent.replace('_agent', '').replace('_classifier', '')}</span>
              </div>
            ))}
          </div>

          {/* Agents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {statusData.agents.map((agent) => {
              const info = agentNames[agent.agent_id] || { label: agent.role, icon: Cpu, desc: agent.role };
              const IconComp = info.icon;
              return (
                <div
                  key={agent.agent_id}
                  className="bg-white rounded-xl p-4 border border-gray-200 shadow-xs hover:border-indigo-300 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-indigo-50 text-indigo-700 font-bold">
                          <IconComp className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-bold text-sm text-gray-900">{info.label}</h4>
                          <span className="text-xs text-gray-500 block">{info.desc}</span>
                        </div>
                      </div>
                      {getStatusBadge(agent.status)}
                    </div>

                    <div className="mt-3.5 pt-3 border-t border-gray-100 space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">{lang === 'hi' ? 'अंतिम कार्य:' : 'Last Action:'}</span>
                        <span className="font-medium text-gray-800 max-w-[190px] truncate text-right" title={agent.last_action}>
                          {agent.last_action || 'Standing by'}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">{lang === 'hi' ? 'कुल निष्पादन:' : 'Processed Count:'}</span>
                        <span className="font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                          {agent.total_processed} items
                        </span>
                      </div>
                      {agent.last_execution_ms > 0 && (
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-500">{lang === 'hi' ? 'प्रतिक्रिया समय:' : 'Execution Time:'}</span>
                          <span className="font-mono text-gray-700">{agent.last_execution_ms} ms</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {agent.tools_registered && agent.tools_registered.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-gray-100 flex flex-wrap gap-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider w-full mb-0.5">
                        {lang === 'hi' ? 'सक्रिय टूल्स (Hermes Function Calls):' : 'Registered Hermes Tools:'}
                      </span>
                      {agent.tools_registered.map((tName, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[11px] font-mono border border-gray-200">
                          ⚡ {tName}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="p-6 text-center text-red-500">Failed to load agent status. Ensure backend is running on port 8000.</div>
      )}
    </div>
  );
}
