import { useState } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';

// 诱饵库：前端硬编码，拦截无效API调用，省下每一分钱成本
const HEXAGRAMS = [
  {
    number: "01",
    sc: { name: "乾为天", insight: "商业与职涯皆有周期，需按部就班从潜伏蓄力到适时出击，严防盛极而衰。" },
    tc: { name: "乾為天", insight: "商業與職涯皆有週期，需按部就班從潛伏蓄力到適時出擊，嚴防盛極而衰。" }
  },
  {
    number: "02",
    sc: { name: "坤为地", insight: "谨守副手定位，不抢主导权，以极致的底层执行力成全团队大局。" },
    tc: { name: "坤為地", insight: "謹守副手定位，不搶主導權，以完美的底層執行力成全整體大局。" }
  },
  {
    number: "03",
    sc: { name: "水雷屯", insight: "草创阶段寸步难行，必须步步为营，先稳固核心根基，再谋求外部扩张。" },
    tc: { name: "水雷屯", insight: "草創階段寸步難行，必須步步為營，先穩固核心根基，再謀求外部擴張。" }
  },
  {
    number: "04",
    sc: { name: "山水蒙", insight: "破除认知盲区，建立主动解决问题的自驱力，而非被动等待Boss指示。" },
    tc: { name: "山水蒙", insight: "破除認知盲區，建立主動發現與解決問題的自驅力，而非被動等待指示。" }
  },
  {
    number: "05",
    sc: { name: "水天需", insight: "顺应客观时势耐心等待，以正规路径满足需求，戒除任何急躁与越界。" },
    tc: { name: "水天需", insight: "順應客觀時勢耐心等待，以正規路徑滿足需求，戒除任何急躁與越界。" }
  },
  {
    number: "06",
    sc: { name: "天水讼", insight: "利益冲突中尽量化干戈为玉帛，诉诸底线与死磕到底必致双输。" },
    tc: { name: "天水訟", insight: "利益衝突中應盡量化干戈為玉帛，訴諸底線與堅持死咬必致雙輸。" }
  },
  {
    number: "07",
    sc: { name: "地水师", insight: "激烈的红海竞争必须师出有名，以正当手段获取市场共识与团队纪律。" },
    tc: { name: "地水師", insight: "激烈的紅海競爭必須師出有名，以正當手段獲取市場共識與團隊紀律。" }
  },
  {
    number: "08",
    sc: { name: "水地比", insight: "慎重选择商业盟友，以诚信结盟，同时保持理性的距离与进退弹性。" },
    tc: { name: "水地比", insight: "慎重選擇商業盟友，以誠信結盟，同時保持理性的距離與進退彈性。" }
  },
  {
    number: "09",
    sc: { name: "风天小畜", insight: "资源的初步积累期，需量力而行，并懂得适时让利以换取长期支持。" },
    tc: { name: "風天小畜", insight: "資源的初步累積期，需量力而為，並懂得適時讓利以換取長期支持。" }
  },
  {
    number: "10",
    sc: { name: "天泽履", insight: "伴君如伴虎，需恪守商业规则与阶层秩序，步步为营以规避高危风险。" },
    tc: { name: "天澤履", insight: "伴君如伴虎，需恪守商業規則與階層秩序，步步為營以規避高危風險。" }
  },
  {
    number: "11",
    sc: { name: "地天泰", insight: "顺境中必须居安思危，亲近优质资源，并主动下沉与基层保持信息畅通。" },
    tc: { name: "地天泰", insight: "順境中必須居安思危，親近優質資源，並主動下沉與基層保持資訊暢通。" }
  },
  {
    number: "12",
    sc: { name: "天地否", insight: "逆境与有毒的职场环境中切忌强出头，明哲保身，收敛锋芒以等待周期反转。" },
    tc: { name: "天地否", insight: "逆境與有害的職場環境中切忌強出頭，明哲保身，收斂鋒芒以等待週期反轉。" }
  },
  {
    number: "13",
    sc: { name: "天火同人", insight: "秉持绝对公心打破部门壁垒，以透明的宏大愿景凝聚跨部门同盟。" },
    tc: { name: "天火同人", insight: "秉持絕對公心打破部門穀倉 (Silos)，以宏觀透明的願景凝聚廣泛同盟。" }
  },
  {
    number: "14",
    sc: { name: "火天大有", insight: "掌握绝对垄断资源后，必须懂得利润普照与利益分享，方能稳固护城河。" },
    tc: { name: "火天大有", insight: "掌握絕對壟斷資源後，必須懂得利潤普照與利益分享，方能穩固競爭壁壘。" }
  },
  {
    number: "15",
    sc: { name: "地山谦", insight: "实力越强姿态必须越低，以向下兼容和出让风头换取长久的系统安全感。" },
    tc: { name: "地山謙", insight: "實力越強姿態必須越低，以謙卑包容和出讓鋒芒換取長久的系統安全感。" }
  },
  {
    number: "16",
    sc: { name: "雷地豫", insight: "准确预判风口并顺势造势，但绝不可在狂热的红利期中丧失理智与备用预案。" },
    tc: { name: "雷地豫", insight: "準確預判風口並順勢造勢，但絕不可在狂熱的紅利期中喪失理智與備案機制。" }
  },
  {
    number: "17",
    sc: { name: "泽雷随", insight: "周期更替时果断抛弃历史包袱，顺应市场新逻辑与新的权力中心。" },
    tc: { name: "澤雷隨", insight: "週期更替時果斷拋棄歷史包袱，順應市場新邏輯與新的權力中心。" }
  },
  {
    number: "18",
    sc: { name: "山风蛊", insight: "面对内部组织沉疴必须刮骨疗毒，先进行周密调研，后实施强力监督的彻底改革。" },
    tc: { name: "山風蠱", insight: "面對內部組織沉痾必須刮骨療毒，先進行周密市調，後實施強力監督的徹底改革。" }
  },
  {
    number: "19",
    sc: { name: "地泽临", insight: "管理者须亲自下沉业务一线，在短暂的红利窗口期内极速抢收业绩。" },
    tc: { name: "地澤臨", insight: "管理者須親自視察業務第一線，在短暫的紅利窗口期內極速搶收業績。" }
  },
  {
    number: "20",
    sc: { name: "风地观", insight: "战略迷茫期立即停止战术上的盲目勤奋，拉高视角，洞察宏观基本面后再做决策。" },
    tc: { name: "風地觀", insight: "策略迷茫期應立即停止戰術上的盲目勤奮，拉高視角，洞察總體基本面後再做決策。" }
  },
  {
    number: "21",
    sc: { name: "火雷噬嗑", insight: "清理违规与内耗必须动用雷霆手段，以硬性规则立威，绝不妥协退让。" },
    tc: { name: "火雷噬嗑", insight: "清理違規與內部消耗必須動用雷霆手段，以硬性規則立威，絕不妥協退讓。" }
  },
  {
    number: "22",
    sc: { name: "山火贲", insight: "适度进行品牌包装，但商业底牌最终必须回归极致的硬核产品力。" },
    tc: { name: "山火賁", insight: "適度進行品牌包裝，但商業底牌最終必須回歸極致的硬核產品力。" }
  },
  {
    number: "23",
    sc: { name: "山地剥", insight: "遭遇系统性衰退时，果断切断边缘业务，死守核心现金流与底线人才。" },
    tc: { name: "山地剝", insight: "遭遇系統性衰退時，果斷切斷邊緣業務，死守核心現金流與底線人才。" }
  },
  {
    number: "24",
    sc: { name: "地雷复", insight: "触底反弹的初始阶段必须极致克制，闭关休养，小心呵护微弱的增长点。" },
    tc: { name: "地雷復", insight: "觸底反彈的初始階段必須極致克制，閉關休養，小心呵護微弱的成長動能。" }
  },
  {
    number: "25",
    sc: { name: "天雷无妄", insight: "彻底放弃捷径与投机心理，恪守商业常识与合规底线，方能免除飞来横祸。" },
    tc: { name: "天雷無妄", insight: "徹底放棄捷徑與投機心理，恪守商業常識與法遵底線，方能免除飛來橫禍。" }
  },
  {
    number: "26",
    sc: { name: "山天大畜", insight: "在资源极度丰厚时更要保持战略定力，蓄而不发，等待行业大拐点。" },
    tc: { name: "山天大畜", insight: "在資源極度豐厚時更要保持策略定力，蓄而不發，等待產業大拐點。" }
  },
  {
    number: "27",
    sc: { name: "山雷颐", insight: "严格控制现金流损耗与公关发声口径，优化内外部生态的供养与被供养关系。" },
    tc: { name: "山雷頤", insight: "嚴格控管現金流損耗與公關發言尺度，優化內外部生態的供養與被供養關係。" }
  },
  {
    number: "28",
    sc: { name: "泽风大过", insight: "极限承压的生死关头，必须果断打破常规，动用超常手段断臂求生。" },
    tc: { name: "澤風大過", insight: "極限承壓的生死關頭，必須果斷打破常規，動用超常手段斷尾求生。" }
  },
  {
    number: "29",
    sc: { name: "坎为水", insight: "连环危机中放弃正面硬刚，顺应险势渗透，死守内核信用以熬过严冬。" },
    tc: { name: "坎為水", insight: "連環危機中放棄正面衝突，順應險勢滲透，死守核心信用以熬過嚴冬。" }
  },
  {
    number: "30",
    sc: { name: "离为火", insight: "个体价值必须深度依附于核心平台或强力生态，方能持续发光发热。" },
    tc: { name: "離為火", insight: "個體價值必須深度依附於核心平台或強力生態，方能持續發光發熱。" }
  },
  {
    number: "31",
    sc: { name: "泽山咸", insight: "放下功利算计，以真诚的同理心跨界破冰，方能引发市场自发的深度共鸣。" },
    tc: { name: "澤山咸", insight: "放下功利算計，以真誠的同理心跨界破冰，方能引發市場自發的深度共鳴。" }
  },
  {
    number: "32",
    sc: { name: "雷风恒", insight: "锁定核心护城河后坚守长期主义，在市场喧嚣中绝不更改战略主轴。" },
    tc: { name: "雷風恆", insight: "鎖定核心護城河後堅守長期主義，在市場喧囂中絕不更改策略主軸。" }
  },
  {
    number: "33",
    sc: { name: "天山遁", insight: "恶劣环境里不可恋战，以最快速度抛售止损，隐蔽撤退以保存核心实力。" },
    tc: { name: "天山遁", insight: "惡劣環境裡不可戀戰，以最快速度拋售停損，隱蔽撤退以保存核心實力。" }
  },
  {
    number: "34",
    sc: { name: "雷天大壮", insight: "占据绝对垄断优势时切忌横冲直撞，必须用规则自我约束以防反噬。" },
    tc: { name: "雷天大壯", insight: "佔據絕對壟斷優勢時切忌橫衝直撞，必須用規則自我約束以防反噬。" }
  },
  {
    number: "35",
    sc: { name: "火地晋", insight: "获得核心资源背书的黄金期，应全方位高调出击，疯狂抢占市场份额。" },
    tc: { name: "火地晉", insight: "獲得核心資源背書的黃金期，應全方位高調出擊，瘋狂搶占市占率。" }
  },
  {
    number: "36",
    sc: { name: "地火明夷", insight: "办公室政治险恶时，必须极度隐忍示弱，装傻自保以求在至暗时刻中生存。" },
    tc: { name: "地火明夷", insight: "辦公室政治險惡時，必須極度隱忍示弱，韜光養晦以求在至暗時刻中生存。" }
  },
  {
    number: "37",
    sc: { name: "风火家人", insight: "对外扩张前先稳固后方，建立权责清晰且高度互信的内部组织机制。" },
    tc: { name: "風火家人", insight: "對外擴張前先穩固後方，建立權責清晰且高度互信的內部組織機制。" }
  },
  {
    number: "38",
    sc: { name: "火泽暌", insight: "面对内部利益分歧不强求理念统一，以共同的 KPI 为纽带求同存异。" },
    tc: { name: "火澤睽", insight: "面對內部利益分歧不強求理念統一，以共同的績效指標 (KPI) 為紐帶求同存異。" }
  },
  {
    number: "39",
    sc: { name: "水山蹇", insight: "遭遇无法跨越的系统性壁垒时，果断后撤，停止无效内耗，退而充实硬实力。" },
    tc: { name: "水山蹇", insight: "遭遇無法跨越的系統性障礙時，果斷後撤，停止無效內耗，退而充實硬實力。" }
  },
  {
    number: "40",
    sc: { name: "雷水解", insight: "危机解除后，必须火速扫除遗留的内部摩擦与历史积怨，恢复组织灵活性。" },
    tc: { name: "雷水解", insight: "危機解除後，必須火速掃除殘留的內部摩擦與歷史積怨，恢復組織靈活性。" }
  },
  {
    number: "41",
    sc: { name: "山泽损", insight: "果断削减低效边缘 Project，牺牲短期利益以换取核心竞争力的长远增值。" },
    tc: { name: "山澤損", insight: "果斷裁撤低效邊緣業務，犧牲短期利益以換取核心競爭力的長遠增值。" }
  },
  {
    number: "42",
    sc: { name: "风雷益", insight: "乘风口大举扩张的同时，必须建立利益共享机制以收拢上下游人心。" },
    tc: { name: "風雷益", insight: "乘風口大舉擴張的同時，必須建立利益共享機制以收攏上下游人心。" }
  },
  {
    number: "43",
    sc: { name: "泽天夬", insight: "面对严重拖累组织的负面资产，必须通过公开且强硬的手段彻底剥离。" },
    tc: { name: "澤天夬", insight: "面對嚴重拖累組織的負面資產，必須透過公開且強硬的手段徹底剝離。" }
  },
  {
    number: "44",
    sc: { name: "天风姤", insight: "面对突然降临的诱人机遇，必须保持最高警惕，以极小规模测试防范暗雷。" },
    tc: { name: "天風姤", insight: "面對突然降臨的誘人機遇，必須保持最高警惕，以極小規模測試防範暗雷。" }
  },
  {
    number: "45",
    sc: { name: "泽地萃", insight: "依托核心平台聚合生态资源，以极度公平的利益分配机制稳固凝聚力。" },
    tc: { name: "泽地萃", insight: "依託核心平台聚合生態資源，以極度公平的利益分配機制穩固凝聚力。" }
  },
  {
    number: "46",
    sc: { name: "地风升", insight: "处于上升通道时拒绝激进跃进，以按部就班的节奏实现阶层的稳健跨越。" },
    tc: { name: "地風昇", insight: "處於上昇通道時拒絕激進盲進，以按部就班的節奏實現階層的穩健跨越。" }
  },
  {
    number: "47",
    sc: { name: "泽水困", insight: "资源枯竭时坚守底线，通过极度透明的高频沟通换取最后一线生机。" },
    tc: { name: "澤水困", insight: "資源枯竭時堅守底線，透過極度透明的高頻溝通換取最後一線生機。" }
  },
  {
    number: "48",
    sc: { name: "水风井", insight: "停止盲目跨界，持续深挖自身核心护城河，确保底层交付能力永不枯竭。" },
    tc: { name: "水風井", insight: "停止盲目跨界，持續深挖自身核心護城河，確保底層交付能力永不枯竭。" }
  },
  {
    number: "49",
    sc: { name: "泽火革", insight: "行业红利耗尽时，必须带着破釜沉舟的勇气进行彻底的自我颠覆与模式重组。" },
    tc: { name: "澤火革", insight: "產業紅利耗盡時，必須帶著破釜沉舟的勇氣進行徹底的自我顛覆與模式重組。" }
  },
  {
    number: "50",
    sc: { name: "火风鼎", insight: "创新成功后，火速将经验固化为行业标准与内部 SOP，确立新的管理秩序。" },
    tc: { name: "火風鼎", insight: "創新成功後，火速將經驗固化為產業標準與內部 SOP，確立新的管理秩序。" }
  },
  {
    number: "51",
    sc: { name: "震为雷", insight: "遭遇突发巨震时保持绝对镇定，化危机为重塑管理权威与内部洗牌的契机。" },
    tc: { name: "震為雷", insight: "遭遇突發震撼時保持絕對鎮定，化危機為重塑管理權威與內部洗牌的契機。" }
  },
  {
    number: "52",
    sc: { name: "艮为山", insight: "认清能力与资源的边界，设立绝对止损线，坚守核心阵地绝不盲目越界。" },
    tc: { name: "艮為山", insight: "認清能力與資源的邊界，設立絕對停損線，堅守核心陣地絕不盲目越界。" }
  },
  {
    number: "53",
    sc: { name: "风山渐", insight: "追求长期主义的稳健复利，抵制一夜暴富的诱惑，依靠时间沉淀业务壁垒。" },
    tc: { name: "風山漸", insight: "追求長期主義的穩健複利，抵制一夜暴富的誘惑，依靠時間沉澱業務壁壘。" }
  },
  {
    number: "54",
    sc: { name: "雷泽归妹", insight: "在并购或合作中认清从属地位，绝不越权，以不可替代的配合度换取生存。" },
    tc: { name: "雷澤歸妹", insight: "在併購或合作中認清從屬地位，絕不越權，以不可替代的配合度換取生存。" }
  },
  {
    number: "55",
    sc: { name: "雷火丰", insight: "处于业绩巅峰时绝不傲慢，强制将超额利润转化为穿越下个周期的技术储备。" },
    tc: { name: "雷火豐", insight: "處於業績巔峰時絕不傲慢，強制將超額利潤轉化為穿越下個週期的技術儲備。" }
  },
  {
    number: "56",
    sc: { name: "火山旅", insight: "进入陌生市场或基于 Project 的组织架构中，必须保持极轻资产运作，广结善缘不树强敌。" },
    tc: { name: "火山旅", insight: "進入陌生市場或專案制辦公，必須保持極輕資產運作，廣結善緣不樹強敵。" }
  },
  {
    number: "57",
    sc: { name: "巽为风", insight: "放弃生硬强压，通过高频、温和的沟通将战略意志渗透至组织的每一根毛细血管。" },
    tc: { name: "巽為風", insight: "放棄生硬強壓，透過高頻、溫和的溝通將策略意志滲透至組織的每一根微血管。" }
  },
  {
    number: "58",
    sc: { name: "兑为泽", insight: "建立无障碍且充满情绪价值的内部沟通机制，以共赢愿景驱动团队自发战斗。" },
    tc: { name: "兌為澤", insight: "建立無障礙且充滿情緒價值的內部溝通機制，以共贏願景驅動團隊自發戰鬥。" }
  },
  {
    number: "59",
    sc: { name: "风水涣", insight: "强力打散臃肿的部门墙与官僚架构，将权力下放，重新激活一线的灵活性。" },
    tc: { name: "風水渙", insight: "強力打散臃腫的部門穀倉與官僚架構，將權力下放，重新激活第一線的靈活性。" }
  },
  {
    number: "60",
    sc: { name: "水泽节", insight: "设立极其严格的 Budget 红线与审批制度，用适度的克制换取现金流的持久健康。" },
    tc: { name: "水澤節", insight: "設立極其嚴格的預算紅線與簽核制度，用適度的克制換取現金流的持久健康。" }
  },
  {
    number: "61",
    sc: { name: "风泽中孚", insight: "以绝对的透明与契约精神对待上下游，将品牌信誉打造成应对危机的最终护城河。" },
    tc: { name: "風澤中孚", insight: "以絕對的透明與契約精神對待上下游，將品牌信譽打造成應對危機的最終護城河。" }
  },
  {
    number: "62",
    sc: { name: "雷山小过", insight: "大局已定阶段放弃宏大冒险，将所有精力聚焦于微观执行细节的极致打磨。" },
    tc: { name: "雷山小過", insight: "大局已定階段放棄宏大冒險，將所有精力聚焦於微觀執行細節的極致打磨。" }
  },
  {
    number: "63",
    sc: { name: "水火既济", insight: "业务大功告成之际，必须立即启动防守预案，严防团队懈怠与完美状态的坍塌。" },
    tc: { name: "水火既濟", insight: "專案大功告成之際，必須立即啟動防守預案，嚴防團隊懈怠與完美狀態的坍塌。" }
  },
  {
    number: "64",
    sc: { name: "火水未济", insight: "商业永远没有终点，将每一次胜利视为新周期的开始，永葆探索未知的警醒。" },
    tc: { name: "火水未濟", insight: "商業永遠沒有終點，將每一次勝利視為新週期的開始，永保探索未知的警醒。" }
  }
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [region, setRegion] = useState("台灣/港澳");
  const [hexagram, setHexagram] = useState(null);
  const [password, setPassword] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fullReport, setFullReport] = useState("");

  // 第一性原理：衍生状态 (Derived State)
  // 根据用户选择的地区，动态决定当前语言键，无需使用 useEffect 监听
  const lang = region.includes("台灣") ? "tc" : "sc";

  const handleGenerate = () => {
    if (!question.trim()) {
      return alert(lang === "tc" ? "請輸入具體問題" : "请输入具体问题");
    }
    const random = Math.floor(Math.random() * HEXAGRAMS.length);
    setHexagram(HEXAGRAMS[random]);
    setUnlocked(false);
    setFullReport("");
  };

  const handleUnlock = async () => {
    if (password.trim() !== "AURA-888") {
      return alert(lang === "tc" ? "密碼驗證失敗，請確認購買後的感謝信內容。" : "密码验证失败，请确认购买后的感谢信内容。");
    }
    setUnlocked(true);
    setLoading(true);

    try {
      const response = await fetch('/api/dify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputs: {
            User_Question: question,
            Region: region,
            // 动态向大模型传入当前简中的卦名，确保知识库语言匹配
            Hexagram_Name: hexagram["sc"].name 
          },
          response_mode: "blocking",
          user: "web_user_" + Date.now()
        })
      });

      const data = await response.json();
      
      if (data && data.data && data.data.outputs) {
        let finalContent = data.data.outputs.Report || data.data.outputs.text || data.data.outputs.answer;
        
        if (finalContent) {
           // 【核心新增】：使用正则清洗掉 <think> 标签及其内部的所有换行与文字，并去除首尾空白
           finalContent = finalContent.replace(/<think>[\s\S]*?<\/think>\n*/gi, '').trim();
           
           setFullReport(finalContent);
        } else {
           setFullReport(lang === "tc" ? "⚠️ 數據解析失敗：找不到對應的輸出內容。" : "⚠️ 数据解析失败：找不到对应的输出内容。");
        }
      }
    } catch (error) {
      setFullReport(lang === "tc" ? "系統繁忙，請稍後重試。" : "系统繁忙，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#333333] font-sans p-6 selection:bg-gray-200">
      <div className="max-w-md mx-auto space-y-8 mt-12">
        
        <header className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-widest text-gray-900">
            {lang === "tc" ? "決策之書" : "决策之书"}
          </h1>
          <p className="text-xs text-gray-500 tracking-[0.2em]">
            {lang === "tc" ? "AI 宇宙能量推演模型" : "AI 宇宙能量推演模型"}
          </p>
        </header>

        <section className="space-y-4">
          <textarea 
            className="w-full p-4 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-400 bg-white shadow-sm resize-none"
            rows="3"
            placeholder={lang === "tc" ? "請輸入你當下最糾結的抉擇..." : "请输入你当下最纠结的抉择..."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />

          <select 
            className="w-full p-3 border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-gray-400"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            <option value="台灣/港澳">台灣/港澳地區 (繁體)</option>
            <option value="新加坡/大馬">新加坡/大馬地区 (简体)</option>
          </select>

          <button 
            onClick={handleGenerate}
            className="w-full bg-[#1A1A1A] text-white py-3.5 rounded-lg tracking-widest font-medium hover:bg-black transition-colors"
          >
            {lang === "tc" ? "生成推演報告" : "生成推演报告"}
          </button>
        </section>

        {hexagram && (
          <section className="mt-8 border border-gray-200 p-6 rounded-xl bg-white relative overflow-hidden shadow-sm">
            {/* 序号与卦名的视觉分层 */}
            <div className="flex items-baseline space-x-3 mb-2">
              <span className="text-3xl font-black text-gray-200 select-none">
                {hexagram.number}
              </span>
              <h2 className="text-lg font-bold">
                🔮 {lang === "tc" ? "你的能量切片：" : "你的能量切片："}{hexagram[lang].name}
              </h2>
            </div>
            
            <p className="text-sm font-medium text-gray-600 mb-6 leading-relaxed">
              {hexagram[lang].insight}
            </p>

            {unlocked ? (
              <div className="mt-6 whitespace-pre-wrap text-sm text-gray-700 leading-relaxed border-t border-gray-100 pt-4">
                {loading ? (
                  <span className="animate-pulse flex items-center space-x-2">
                    <span className="h-2 w-2 bg-gray-400 rounded-full"></span>
                    <span className="h-2 w-2 bg-gray-400 rounded-full animation-delay-200"></span>
                    <span className="h-2 w-2 bg-gray-400 rounded-full animation-delay-400"></span>
                    <span className="ml-2">
                      {lang === "tc" ? "正在構建高維度決策報告..." : "正在构建高维度决策报告..."}
                    </span>
                  </span>
                ) : fullReport}
              </div>
            ) : (
              <div className="relative mt-6 border-t border-gray-100 pt-4">
                <div className="blur-sm text-gray-400 text-sm leading-relaxed select-none opacity-60">
                  {lang === "tc" ? (
                    <>
                      【現狀刺透】這裏將輸出深度分析文本，直擊你的核心痛點與處境。<br/><br/>
                      【避坑指南】這裏是商業紅線警告，告訴你在此抉擇下絕對不能做什麽。<br/><br/>
                      【破局行動】這裏是符合第一性原理的具體實操建議。<br/><br/>
                      【未來演進】這裏是對未來三個月客觀趨勢的推演。
                    </>
                  ) : (
                    <>
                      【现状刺透】这里将输出深度分析文本，直击你的核心痛点与处境。<br/><br/>
                      【避坑指南】这里是商业红线警告，告诉你在此抉择下绝对不能做什么。<br/><br/>
                      【破局行动】这里是符合第一性原理的具体实操建议。<br/><br/>
                      【未来演进】这里是对未来三个月客观趋势的推演。
                    </>
                  )}
                </div>
                
                <div className="absolute inset-0 flex flex-col items-center justify-center p-4 bg-white/50 backdrop-blur-xs">
                  <a 
                    href="https://ko-fi.com/s/your-product-link" 
                    target="_blank" 
                    rel="noreferrer"
                    className="mb-5 text-sm font-bold text-[#7C2D12] underline hover:text-black transition-colors"
                  >
                    🛒 {lang === "tc" ? "支付 $3.99 獲取本週解鎖密碼" : "支付 $3.99 获取本周解锁密码"}
                  </a>
                  <input 
                    type="text" 
                    placeholder={lang === "tc" ? "輸入解鎖密碼" : "输入解锁密码"} 
                    className="w-full max-w-[220px] text-center p-2.5 border border-gray-300 rounded-md mb-4 bg-white/90 focus:outline-none"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button 
                    onClick={handleUnlock}
                    className="bg-[#1A1A1A] text-white px-8 py-2.5 rounded-md text-sm font-medium hover:bg-black transition-colors"
                  >
                    {lang === "tc" ? "解鎖深度推演" : "解锁深度推演"}
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
      </div>
      <Analytics />
      <SpeedInsights />
    </div>
  );
}