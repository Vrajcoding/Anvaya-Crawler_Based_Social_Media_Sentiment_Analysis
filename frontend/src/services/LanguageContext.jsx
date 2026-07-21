import React, { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext();

export const translations = {
  hi: {
    // Top Bar & Header
    gov_top_title: "🇮🇳 भारत सरकार",
    gov_top_dept: "गृह विभाग (गुजरात राज्य)",
    cyber_helpline: "साइबर हेल्पलाइन: 1930 / 079-23254300",
    text_size_large: "🔍 बड़ा टेक्स्ट (A+)",
    text_size_normal: "🔍 सामान्य टेक्स्ट (A-)",
    portal_title: "SentinelAI — राष्ट्रीय सोशल मीडिया सुरक्षा एवं खतरा विश्लेषक",
    portal_subtitle: "राष्ट्रीय सोशल मीडिया खतरा एवं इंटेलिजेंस निगरानी पोर्टल (ERH26_PS_05)",
    on_duty_label: "ड्यूटी अधिकारी:",
    duty_officer_name: "इंसपेक्टर आर. के. पटेल (सूरत साइबर सेल)",
    btn_sync_data: "डेटा अपडेट करें",
    
    // Nav Tabs
    nav_dashboard: "🏠 मुख्य डैशबोर्ड",
    nav_alerts: "🚨 आपातकालीन अलर्ट",
    nav_feed: "📰 सोशल मीडिया लाइव फीड",
    nav_trends: "📈 अफवाहें और ट्रेंड",
    nav_network: "🕸️ संदिग्ध बॉट नेटवर्क",
    nav_watchlist: "🎯 निगरानी सूची",
    nav_reports: "📄 सरकारी पुलिस रिपोर्ट",
    nav_settings: "⚙️ एआई नियंत्रण व सेटिंग्स",
    
    // Emergency Banner
    emergency_banner_title: "🚨 आपातकालीन अलर्ट (गंभीर खतरा):",
    btn_view_alert: "अलर्ट कतार में देखें",
    
    // Dashboard Stats & Headers
    dash_stats_monitored: "कुल मॉनिटर की गई पोस्ट",
    dash_stats_critical: "गंभीर एवं उच्च खतरा स्कोर",
    dash_stats_rumors: "सक्रिय वायरल अफवाहें",
    dash_stats_bots: "चिह्नित बॉट नेटवर्क खाते",
    dash_live_feed_title: "ताज़ा सोशल मीडिया थ्रेट फीड",
    dash_threat_dist_title: "खतरा श्रेणी वितरण",
    dash_platform_dist_title: "मंच अनुसार पोस्ट वितरण",
    
    // Threat Feed Page
    feed_page_title: "📰 रीयल-टाइम सोशल मीडिया इंटेलिजेंस फीड",
    feed_page_subtitle: "ओपनराउटर एआई व लाइव क्रॉलर द्वारा सभी सोशल प्लेटफॉर्म्स (X, Facebook, Instagram, YouTube) की निगरानी",
    filter_all: "सभी पोस्ट",
    filter_critical: "गंभीर खतरा",
    filter_incitement: "हिंसा भड़काना",
    filter_fakenews: "फ़ेक न्यूज़ / अफवाह",
    filter_hate: "हेट स्पीच",
    
    // Presets & Tester
    preset_quick_search: "त्वरित खोज फ़िल्टर (पुलिस हेतु):",
    preset_surat: "📍 सूरत",
    preset_stone_pelting: "🧱 पत्थरबाजी",
    preset_water_poison: "⚠️ पानी में जहर अफवाह",
    preset_riots_call: "🔥 दंगा उकसावा",
    test_text_title: "संदिग्ध संदेश का AI विश्लेषण करें",
    test_text_desc: "व्हाट्सएप या सोशल मीडिया का कोई भी संदिग्ध संदेश यहाँ पेस्ट करके जांचें:",
    test_text_placeholder: "उदा: कल रात 10 बजे मुख्य चौक पर सब पत्थर लेकर पहुंचे!",
    btn_analyze: "विश्लेषण करें",
    btn_analyzing: "विश्लेषण जारी...",
    analysis_complete: "विश्लेषण परिणाम:",
    label_platform: "प्लेटफ़ॉर्म:",
    label_threat_level: "खतरा स्तर:",
    label_language: "भाषा:",
    all_platforms: "सभी प्लेटफ़ॉर्म",
    all_languages: "सभी भाषाएं",
    inflammatory: "भड़काऊ",
    neutral: "सामान्य",
    search_placeholder: "खोजें (पाठ या खाता)...",
    no_posts_found: "चयनित फ़िल्टर के अनुसार कोई पोस्ट नहीं मिली।",
    
    // Alerts Page
    alerts_page_title: "🚨 आपातकालीन साइबर अलर्ट एवं त्वरित कार्रवाई केंद्र",
    alerts_page_subtitle: "उच्च एवं गंभीर श्रेणी के सामाजिक खतरों के लिए स्वचालित एआई एस्केलेशन कतार",
    alert_status_open: "सक्रिय (OPEN)",
    alert_status_ack: "संज्ञान लिया गया",
    alert_status_resolved: "कार्रवाई पूर्ण",
    btn_ack: "संज्ञान लें",
    btn_resolve: "कार्रवाई पूर्ण करें",
    btn_escalate_dgp: "⚡ डीजीपी व क्राइम ब्रांच को एस्केलेट करें",
    
    // Watchlist Page
    watchlist_page_title: "🎯 अति-संवेदनशील निगरानी सूची प्रबंधक",
    watchlist_page_subtitle: "विशेष निगरानी हेतु संवेदनशील कीवर्ड, हैशटैग एवं संदिग्ध सोशल प्रोफाइल जोड़ें",
    wl_add_target: "नया निगरानी लक्ष्य जोड़ें",
    wl_active_targets: "वर्तमान सक्रिय निगरानी लक्ष्य",
    wl_btn_add: "लक्ष्य जोड़ें",
    wl_btn_remove: "हटाएं",
    wl_type: "प्रकार",
    wl_value: "कीवर्ड / लक्ष्य",
    wl_platform: "प्लेटफ़ॉर्म",
    wl_geo: "लक्षित क्षेत्र",
    wl_priority: "प्राथमिकता",
    wl_actions: "कार्रवाई",
    
    // Reports Page
    reports_page_title: "📄 सरकारी पुलिस थ्रेट रिपोर्ट जनरेटर",
    reports_page_subtitle: "उच्चाधिकारियों एवं वरिष्ठ कमान को प्रस्तुत करने हेतु औपचारिक साइबर रिपोर्ट तैयार करें",
    report_compile_title: "नई पुलिस इंटेलिजेंस रिपोर्ट तैयार करें",
    report_btn_generate: "सरकारी रिपोर्ट जनरेट करें",
    report_title_placeholder: "रिपोर्ट का शीर्षक (उदा: सूरत चौक बाज़ार हिंसा अफवाह विश्लेषण)",
    report_desc_placeholder: "घटना का संक्षिप्त विवरण एवं पुलिस जांच बिंदु...",
    
    // Trend Analysis Page
    trends_page_title: "📈 अफवाहें एवं स्पाइक ट्रेंड विश्लेषण",
    trends_page_subtitle: "क्षेत्रीय हैशटैग, भड़काऊ कीवर्ड एवं अपरिमेय उछाल (Z-score spike) का स्वचालित मापन",
    trends_chart_title: "📊 ट्रेंडिंग हैशटैग आयतन व गति",
    trends_spiking_tags: "🔥 तेजी से फैलते हैशटैग",
    trends_sensitive_keywords: "⚠️ निगरानी योग्य संवेदनशील शब्द",
    viral_velocity: "वायरल गति",
    sentiment_index: "जनभावना सूचकांक",
    
    // Network View Page
    network_page_title: "🕸️ संदिग्ध गैंग व बॉट नेटवर्क विश्लेषक",
    network_page_subtitle: "एक साथ अफवाह फैलाने वाले फेक अकाउंट्स एवं संगठित साइबर गिरोहों का नेटवर्क ग्राफ",
    net_nodes_title: "संदिग्ध खातों का नेटवर्क मानचित्र",
    net_legend: "सामान्य यूजर | उच्च-खतरा पोस्ट | ऑटोमेटेड बॉट खाता | संगठित शेयर नेटवर्क",
    net_bot_clusters: "स्वचालित बॉट गैंग्स",
    bot_cluster: "बॉट नेटवर्क क्लस्टर",
    mastermind_node: "मुख्य स्रोत / मास्टरमाइंड",
    
    // Settings & OpenRouter Page
    settings_title: "⚙️ ओपनराउटर एआई मल्टी-एजेंट एवं सिस्टम सेटिंग्स",
    settings_subtitle: "रीयल-टाइम LLM इन्फरेंस के लिए ओपनराउटर API कुंजी, फ्री मॉडल्स एवं लाइव क्रॉलर नियंत्रण",
    api_key_label: "ओपनराउटर API कुंजी",
    nlp_model_label: "एनएलपी एवं भाषा विश्लेषण मॉडल",
    threat_model_label: "खतरा वर्गीकरण एवं स्कोरिंग मॉडल",
    report_model_label: "पुलिस इंटेलिजेंस रिपोर्ट मॉडल",
    alert_model_label: "त्वरित आपातकालीन अलर्ट मॉडल",
    btn_save_settings: "सेटिंग्स सुरक्षित करें",
    settings_saved_msg: "✅ ओपनराउटर एआई एवं सिस्टम सेटिंग्स सफलतापूर्वक अपडेट कर दी गई हैं!"
  },
  
  gu: {
    // Top Bar & Header
    gov_top_title: "🇮🇳 ભારત સરકાર",
    gov_top_dept: "ગૃહ વિભાગ (ગુજરાત રાજ્ય)",
    cyber_helpline: "સાયબર હેલ્પલાઇન: 1930 / 079-23254300",
    text_size_large: "🔍 મોટો ટેક્સ્ટ (A+)",
    text_size_normal: "🔍 સામાન્ય ટેક્સ્ટ (A-)",
    portal_title: "SentinelAI — રાષ્ટ્રીય સોશિયલ મીડિયા સુરક્ષા અને જોખમ વિશ્લેષક",
    portal_subtitle: "રાષ્ટ્રીય સોશિયલ મીડિયા જોખમ અને ઇન્ટેલિજન્સ નિરીક્ષણ પોર્ટલ (ERH26_PS_05)",
    on_duty_label: "ડ્યુટી અધિકારી:",
    duty_officer_name: "ઇન્સ્પેક્ટર આર. કે. પટેલ (સુરત સાયબર સેલ)",
    btn_sync_data: "ડેટા અપડેટ કરો",
    
    // Nav Tabs
    nav_dashboard: "🏠 મુખ્ય ડેશબોર્ડ",
    nav_alerts: "🚨 ઈમરજન્સી એલર્ટ",
    nav_feed: "📰 સોશિયલ મીડિયા લાઇવ ફીડ",
    nav_trends: "📈 અફવાઓ અને ટ્રેન્ડ",
    nav_network: "🕸️ શંકાસ્પદ બોટ નેટવર્ક",
    nav_watchlist: "🎯 દેખરેખ સૂચિ",
    nav_reports: "📄 સરકારી પોલીસ રિપોર્ટ",
    nav_settings: "⚙️ એઆઈ નિયંત્રણ અને સેટિંગ્સ",
    
    // Emergency Banner
    emergency_banner_title: "🚨 ઈમરજન્સી એલર્ટ (ગંભીર જોખમ):",
    btn_view_alert: "એલર્ટ કતારમાં જુઓ",
    
    // Dashboard Stats & Headers
    dash_stats_monitored: "કુલ મોનિટર કરેલી પોસ્ટ",
    dash_stats_critical: "ગંભીર અને ઉચ્ચ જોખમ સ્કોર",
    dash_stats_rumors: "સક્રિય વાયરલ અફવાઓ",
    dash_stats_bots: "ચિહ્નિત બોટ નેટવર્ક ખાતા",
    dash_live_feed_title: "તાજેતરની સોશિયલ મીડિયા થ્રેટ ફીડ",
    dash_threat_dist_title: "જોખમ શ્રેણી વિતરણ",
    dash_platform_dist_title: "પ્લેટફોર્મ મુજબ પોસ્ટ વિતરણ",
    
    // Threat Feed Page
    feed_page_title: "📰 રીયલ-ટાઇમ સોશિયલ મીડિયા ઇન્ટેલિજન્સ ફીડ",
    feed_page_subtitle: "ઓપનરાઉટર એઆઈ અને લાઇવ ક્રોલર દ્વારા તમામ સોશિયલ પ્લેટફોર્મ્સ (X, Facebook, Instagram, YouTube) ની સતત દેખરેખ",
    filter_all: "તમામ પોસ્ટ",
    filter_critical: "ગંભીર જોખમ",
    filter_incitement: "હિંસા ઉશ્કેરવી",
    filter_fakenews: "ફેક ન્યૂઝ / અફવા",
    filter_hate: "હેટ સ્પીચ",
    
    // Presets & Tester
    preset_quick_search: "ઝડપી શોધ ફિલ્ટર્સ (પોલીસ માટે):",
    preset_surat: "📍 સુરત",
    preset_stone_pelting: "🧱 પથ્થરમારો",
    preset_water_poison: "⚠️ પાણીમાં ઝેર અફવા",
    preset_riots_call: "🔥 દંગા ઉશ્કેરણી",
    test_text_title: "શંકાસ્પદ સંદેશનું AI વિશ્લેષણ કરો",
    test_text_desc: "વોટ્સએપ અથવા સોશિયલ મીડિયાનો કોઈપણ શંકાસ્પદ સંદેશ અહીં પેસ્ટ કરીને ચકાસો:",
    test_text_placeholder: "દા.ત: કાલે ચોક બજારમાં ઈંટ પથ્થર સાથે રાત્રે 9 વાગે ભેગા થાઓ!",
    btn_analyze: "વિશ્લેષણ કરો",
    btn_analyzing: "વિશ્લેષણ ચાલુ છે...",
    analysis_complete: "વિશ્લેષણ પરિણામ:",
    label_platform: "પ્લેટફોર્મ:",
    label_threat_level: "જોખમ સ્તર:",
    label_language: "ભાષા:",
    all_platforms: "તમામ પ્લેટફોર્મ",
    all_languages: "તમામ ભાષાઓ",
    inflammatory: "ભડકાવનાર",
    neutral: "સામાન્ય",
    search_placeholder: "શોધો (લખાણ અથવા એકાઉન્ટ)...",
    no_posts_found: "પસંદ કરેલા ફિલ્ટર્સ માટે કોઈ પોસ્ટ મળી નથી.",
    
    // Alerts Page
    alerts_page_title: "🚨 ઈમરજન્સી સાયબર એલર્ટ અને ઝડપી કાર્યવાહી કેન્દ્ર",
    alerts_page_subtitle: "ઉચ્ચ અને ગંભીર શ્રેણીના સામાજિક જોખમો માટે સ્વચાલિત એઆઈ એસ્કેલેશન કતાર",
    alert_status_open: "સક્રિય (OPEN)",
    alert_status_ack: "નોંધ લેવાઈ",
    alert_status_resolved: "કાર્યવાહી પૂર્ણ",
    btn_ack: "નોંધ લો",
    btn_resolve: "કાર્યવાહી પૂર્ણ કરો",
    btn_escalate_dgp: "⚡ ડીજીપી અને ક્રાઈમ બ્રાંચને મોકલો",
    
    // Watchlist Page
    watchlist_page_title: "🎯 અતિ-સંવેદનશીલ દેખરેખ સૂચિ મેનેજર",
    watchlist_page_subtitle: "વિશેષ દેખરેખ માટે સંવેદનશીલ કીવર્ડ્સ, હેશટેગ અને પ્રોફાઇલ્સ ઉમેરો",
    wl_add_target: "નવો દેખરેખ લક્ષ્ય ઉમેરો",
    wl_active_targets: "વર્તમાન સક્રિય દેખરેખ લક્ષ્યો",
    wl_btn_add: "લક્ષ્ય ઉમેરો",
    wl_btn_remove: "હટાવો",
    wl_type: "પ્રકાર",
    wl_value: "કીવર્ડ / લક્ષ્ય",
    wl_platform: "પ્લેટફોર્મ",
    wl_geo: "લક્ષિત વિસ્તાર",
    wl_priority: "પ્રાથમિકતા",
    wl_actions: "કાર્યવાહી",
    
    // Reports Page
    reports_page_title: "📄 સરકારી પોલીસ થ્રેટ રિપોર્ટ જનરેટર",
    reports_page_subtitle: "વરિષ્ઠ અધિકારીઓને રજૂ કરવા માટે ઔપચારિક સાયબર રિપોર્ટ તૈયાર કરો",
    report_compile_title: "નવો પોલીસ ઇન્ટેલિજન્સ રિપોર્ટ બનાવો",
    report_btn_generate: "સરકારી રિપોર્ટ જનરેટ કરો",
    report_title_placeholder: "રિપોર્ટનું શીર્ષક (દા.ત: સુરત ચોક બજાર હિંસા અફવા વિશ્લેષણ)",
    report_desc_placeholder: "ઘટનાની સંક્ષિપ્ત વિગત અને પોલીસ તપાસ મુદ્દા...",
    
    // Trend Analysis Page
    trends_page_title: "📈 અફવાઓ અને સ્પાઇક ટ્રેન્ડ વિશ્લેષણ",
    trends_page_subtitle: "પ્રાદેશિક હેશટેગ, ભડકાવનાર કીવર્ડ્સ અને અસામાન્ય ઉછાળનું સ્વચાલિત માપન",
    trends_chart_title: "📊 ટ્રેન્ડિંગ હેશટેગ વોલ્યુમ અને ગતિ",
    trends_spiking_tags: "🔥 ઝડપથી ફેલાતા હેશટેગ",
    trends_sensitive_keywords: "⚠️ દેખરેખ યોગ્ય સંવેદનશીલ શબ્દો",
    viral_velocity: "વાયરલ ગતિ",
    sentiment_index: "જનભાવના સૂચકાંક",
    
    // Network View Page
    network_page_title: "🕸️ શંકાસ્પદ ગેંગ અને બોટ નેટવર્ક વિશ્લેષક",
    network_page_subtitle: "એક સાથે અફવા ફેલાવતા ફેક એકાઉન્ટ્સ અને નેટવર્ક ગ્રાફ",
    net_nodes_title: "શંકાસ્પદ ખાતાઓનો નેટવર્ક નકશો",
    net_legend: "સામાન્ય યુઝર | ઉચ્ચ-જોખમ પોસ્ટ | ઓટોમેટેડ બોટ એકાઉન્ટ | સંકલિત નેટવર્ક",
    net_bot_clusters: "સ્વચાલિત બોટ ગેંગ્સ",
    bot_cluster: "બોટ નેટવર્ક ક્લસ્ટર",
    mastermind_node: "મુખ્ય સ્ત્રોત / માસ્ટરમાઇન્ડ",
    
    // Settings & OpenRouter Page
    settings_title: "⚙️ ઓપનરાઉટર એઆઈ મલ્ટી-એજન્ટ અને સિસ્ટમ સેટિંગ્સ",
    settings_subtitle: "રીયલ-ટાઇમ LLM ઇન્ફરન્સ માટે ઓપનરાઉટર API કી, ફ્રી મોડલ્સ અને લાઇવ ક્રોલર નિયંત્રણ",
    api_key_label: "ઓપનરાઉટર API કી",
    nlp_model_label: "એનએલપી અને ભાષા વિશ્લેષણ મોડલ",
    threat_model_label: "જોખમ વર્ગીકરણ અને સ્કોરિંગ મોડલ",
    report_model_label: "પોલીસ ઇન્ટેલિજન્સ રિપોર્ટ મોડલ",
    alert_model_label: "ઝડપી ઈમરજન્સી એલર્ટ મોડલ",
    btn_save_settings: "સેટિંગ્સ સાચવો",
    settings_saved_msg: "✅ ઓપનરાઉટર એઆઈ અને સિસ્ટમ સેટિંગ્સ સફળતાપૂર્વક અપડેટ કરવામાં આવ્યા છે!"
  },
  
  en: {
    // Top Bar & Header
    gov_top_title: "🇮🇳 Govt. of India | Government Portal",
    gov_top_dept: "Home Department (State of Gujarat)",
    cyber_helpline: "Cyber Control Room Helpline: 1930 / 079-23254300",
    text_size_large: "🔍 Larger Text (A+)",
    text_size_normal: "🔍 Normal Text (A-)",
    portal_title: "SentinelAI — National Social Media Security & Threat Intelligence",
    portal_subtitle: "National Social Media Threat & Intelligence Monitoring Portal (ERH26_PS_05)",
    on_duty_label: "On-Duty Officer:",
    duty_officer_name: "Inspector R. K. Patel (Surat Cyber Cell)",
    btn_sync_data: "Sync Data / Refresh",
    
    // Nav Tabs
    nav_dashboard: "🏠 Main Dashboard",
    nav_alerts: "🚨 Critical Alerts",
    nav_feed: "📰 Social Media Live Feed",
    nav_trends: "📈 Spikes & Rumors Analysis",
    nav_network: "🕸️ Bot Networks & Gang Mapping",
    nav_watchlist: "🎯 Target Watchlist",
    nav_reports: "📄 Official Police CTI Reports",
    nav_settings: "⚙️ AI & OpenRouter Settings",
    
    // Emergency Banner
    emergency_banner_title: "🚨 EMERGENCY CRITICAL ALERT:",
    btn_view_alert: "View Alert Queue",
    
    // Dashboard Stats & Headers
    dash_stats_monitored: "Total Monitored Posts",
    dash_stats_critical: "Critical & High Threat Score",
    dash_stats_rumors: "Active Viral Rumors",
    dash_stats_bots: "Flagged Bot Accounts",
    dash_live_feed_title: "Real-Time Social Media Threat Feed",
    dash_threat_dist_title: "Threat Breakdown",
    dash_platform_dist_title: "Platform Post Distribution",
    
    // Threat Feed Page
    feed_page_title: "📰 Real-Time Social Media Intelligence Feed",
    feed_page_subtitle: "Continuous multi-platform monitoring powered by OpenRouter AI multi-agents and Scrapy/Scapy live crawlers",
    filter_all: "All Posts",
    filter_critical: "Critical Threat",
    filter_incitement: "Incitement to Violence",
    filter_fakenews: "Fake News / Rumors",
    filter_hate: "Hate Speech",
    
    // Presets & Tester
    preset_quick_search: "Quick Search Presets (Police):",
    preset_surat: "📍 Surat",
    preset_stone_pelting: "🧱 Stone Pelting",
    preset_water_poison: "⚠️ Water Poison Rumor",
    preset_riots_call: "🔥 Riots Call",
    test_text_title: "Test Suspicious Text with AI",
    test_text_desc: "Paste any suspicious text from WhatsApp or social media to analyze real-time threat scores:",
    test_text_placeholder: "e.g. Gather at Chowk Bazaar tomorrow with stones at 9 PM!",
    btn_analyze: "Analyze Text",
    btn_analyzing: "Analyzing...",
    analysis_complete: "Analysis Results:",
    label_platform: "Platform:",
    label_threat_level: "Threat Level:",
    label_language: "Language:",
    all_platforms: "All Platforms",
    all_languages: "All Languages",
    inflammatory: "Inflammatory",
    neutral: "Neutral",
    search_placeholder: "Search text or account...",
    no_posts_found: "No posts found for the selected filters.",
    
    // Alerts Page
    alerts_page_title: "🚨 Emergency Cyber Alerts & Rapid Action Command",
    alerts_page_subtitle: "Automated AI escalation queue for high-severity and critical social threats across Indian jurisdictions",
    alert_status_open: "OPEN (Active)",
    alert_status_ack: "ACKNOWLEDGED",
    alert_status_resolved: "RESOLVED",
    btn_ack: "Acknowledge Alert",
    btn_resolve: "Mark Resolved",
    btn_escalate_dgp: "⚡ Escalate to DGP & Crime Branch",
    
    // Watchlist Page
    watchlist_page_title: "🎯 Target Watchlist Manager",
    watchlist_page_subtitle: "24x7 tracking of sensitive keywords, riot hashtags, inflammatory accounts, and locations",
    wl_add_target: "Add New Watchlist Target",
    wl_active_targets: "Currently Active Watchlist Targets",
    wl_btn_add: "Add Target",
    wl_btn_remove: "Remove",
    wl_type: "Type",
    wl_value: "Keyword / Target Value",
    wl_platform: "Platform",
    wl_geo: "Target Location",
    wl_priority: "Priority",
    wl_actions: "Actions",
    
    // Reports Page
    reports_page_title: "📄 Official Police CTI Reports & Briefs",
    reports_page_subtitle: "Formal legal and intelligence briefs synthesized autonomously by OpenRouter AI multi-agent models",
    report_compile_title: "Compile Official Intelligence Report",
    report_btn_generate: "Generate Official Report",
    report_title_placeholder: "Report Title (e.g. Surat Mob Incitement Intelligence Analysis)",
    report_desc_placeholder: "Brief summary of incident and police investigation priorities...",
    
    // Trend Analysis Page
    trends_page_title: "📈 Rumor Spikes & Viral Trend Analysis",
    trends_page_subtitle: "Monitoring rapidly spreading hashtags, coordinated propaganda, and communal sentiment velocity",
    trends_chart_title: "📊 Trending Hashtag Volume & Velocity",
    trends_spiking_tags: "🔥 High Velocity Spiking Hashtags",
    trends_sensitive_keywords: "⚠️ Sensitive High-Risk Keywords",
    viral_velocity: "Viral Velocity",
    sentiment_index: "Public Sentiment Index",
    
    // Network View Page
    network_page_title: "🕸️ Bot Network & Gang Topology",
    network_page_subtitle: "Graph mapping of coordinated troll armies, automated bot clusters, and central propagandist masterminds",
    net_nodes_title: "Identified Network Nodes Map",
    net_legend: "Normal User | Critical Post | Automated Bot Account | Coordinated Network",
    net_bot_clusters: "Automated Bot Gangs",
    bot_cluster: "Bot Network Cluster",
    mastermind_node: "Central Source / Mastermind Node",
    
    // Settings & OpenRouter Page
    settings_title: "⚙️ OpenRouter AI Multi-Agent & System Settings",
    settings_subtitle: "Configure OpenRouter API key, select free/fast LLM inference models, and manage live crawler settings",
    api_key_label: "OpenRouter API Key",
    nlp_model_label: "NLP & Language Analysis Agent Model",
    threat_model_label: "Threat Classifier & Scoring Agent Model",
    report_model_label: "Police CTI Report Generator Agent Model",
    alert_model_label: "Rapid Emergency Alert Dispatch Agent Model",
    btn_save_settings: "Save AI Settings",
    settings_saved_msg: "✅ OpenRouter AI and system settings updated successfully!"
  }
};

export const LanguageProvider = ({ children }) => {
  // Initialize from localStorage so chosen language persists on page refresh!
  const [lang, setLangState] = useState(() => {
    return localStorage.getItem('sentinel_lang') || 'en';
  });

  const setLang = (newLang) => {
    localStorage.setItem('sentinel_lang', newLang);
    setLangState(newLang);
  };

  const t = (key) => {
    return translations[lang]?.[key] || translations['en']?.[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);

