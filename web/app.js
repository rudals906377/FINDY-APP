"use strict";

if (new URLSearchParams(location.search).has("report-capture")) {
  document.documentElement.classList.add("report-capture");
}

const CATEGORIES = ["전체", "헤어", "네일아트", "메이크업", "포토", "웨딩", "반영구시술"];
const CATEGORY_INFO = {
  헤어: ["커트·컬러·펌", "#9a7258", "#d9bda8"],
  네일아트: ["젤·시럽·아트", "#b77075", "#e4c0bb"],
  메이크업: ["데일리·촬영", "#9b647a", "#ddb6c8"],
  포토: ["프로필·스냅", "#566b77", "#aebfc5"],
  웨딩: ["본식·리허설", "#8b725c", "#dacbbd"],
  반영구시술: ["눈썹·립·아이라인", "#75635c", "#c6b3aa"]
};

const SEED_POSTS = [
  {id:"p1",type:"질문",category:"헤어",title:"레이어드컷 손질 쉬운 스타일 추천해주세요",content:"모발이 얇고 아침에 손질할 시간이 많지 않아요. 자연스럽게 얼굴형을 보완하는 스타일이 궁금해요.",author:"봄날",likes:42,saves:11,comments:18,date:"2026-06-23"},
  {id:"p2",type:"리뷰",category:"네일아트",title:"사진으로 보여드린 시럽 네일 느낌 그대로 나왔어요",content:"컬러를 여러 번 비교해주셔서 피부톤에 잘 맞는 조합을 골랐어요. 마감도 얇고 깔끔해서 만족합니다.",author:"밀키",likes:67,saves:24,comments:9,date:"2026-06-22"},
  {id:"p3",type:"자유",category:"메이크업",title:"요즘 좋아하는 맑은 피부 표현 제품 조합",content:"과하게 번들거리지 않고 은은하게 윤기가 도는 조합을 찾았어요. 얇게 여러 번 올리는 게 핵심이네요.",author:"모브",likes:31,saves:17,comments:14,date:"2026-06-21"},
  {id:"p4",type:"질문",category:"웨딩",title:"여름 본식 메이크업에서 가장 중요한 점은 뭘까요?",content:"더위와 조명 때문에 무너짐이 걱정돼요. 리허설 때 꼭 확인해야 할 부분도 알려주세요.",author:"유월",likes:25,saves:8,comments:22,date:"2026-06-20"},
  {id:"p5",type:"리뷰",category:"포토",title:"자연광 프로필 촬영, 표정 디렉팅이 정말 좋았어요",content:"카메라 앞에서 굳는 편인데 대화를 계속 이어가며 편하게 촬영해주셨어요. 필름톤 보정도 마음에 들어요.",author:"소다",likes:53,saves:29,comments:7,date:"2026-06-19"},
  {id:"p6",type:"자유",category:"반영구시술",title:"자연눈썹 받고 아침 준비 시간이 줄었어요",content:"처음에는 진해 보였지만 며칠 지나니 자연스럽게 자리 잡았어요. 디자인 상담을 충분히 하는 게 중요해요.",author:"다온",likes:38,saves:19,comments:11,date:"2026-06-18"}
];

const SNAPS = [
  {id:"s1",category:"헤어",title:"차분한 애쉬브라운 레이어드",likes:284,a:"#8e6b58",b:"#d7b7a1"},
  {id:"s2",category:"네일아트",title:"밀키화이트 자석젤",likes:191,a:"#b67980",b:"#ead6d0"},
  {id:"s3",category:"메이크업",title:"맑고 얇은 코랄 메이크업",likes:326,a:"#9c6576",b:"#e2b2b4"},
  {id:"s4",category:"포토",title:"센치한 필름톤 프로필",likes:147,a:"#52646f",b:"#aab8bb"},
  {id:"s5",category:"웨딩",title:"내추럴 로우번과 피치 메이크업",likes:412,a:"#927968",b:"#d9c8b8"},
  {id:"s6",category:"반영구시술",title:"결을 살린 자연눈썹",likes:233,a:"#685850",b:"#c8b2a8"},
  {id:"s7",category:"헤어",title:"쿨블루 포인트 단발",likes:178,a:"#496278",b:"#9db3c1"},
  {id:"s8",category:"네일아트",title:"투명한 젤리 프렌치",likes:205,a:"#aa7480",b:"#efd6d9"}
];

const VIDEOS = [
  {category:"헤어",title:"앞머리 볼륨 30초 만에 살리는 법",author:"@findy_tip",likes:1284,description:"드라이 방향만 바꿔도 뿌리 볼륨이 훨씬 자연스럽게 살아나요.",a:"#6d4d38",b:"#1d1612"},
  {category:"메이크업",title:"블러 립 경계 자연스럽게 푸는 순서",author:"@mood_makeup",likes:932,description:"립 브러시 대신 손가락 온도를 이용하면 경계가 더 부드러워져요.",a:"#7d4354",b:"#241116"},
  {category:"네일아트",title:"손이 길어 보이는 네일 쉐입 고르기",author:"@nail_note",likes:745,description:"손톱 폭과 큐티클 라인을 기준으로 쉐입을 고르면 실패가 줄어요.",a:"#8a5962",b:"#261719"},
  {category:"포토",title:"증명사진 표정이 어색하지 않는 작은 팁",author:"@photo_room",likes:1108,description:"입술보다 눈 주변의 긴장을 먼저 풀어주는 것이 자연스러운 표정의 핵심이에요.",a:"#435665",b:"#11191f"}
];

const PREFERENCE_DATA = {
  헤어:{moods:["차분한","세련된","내추럴","힙한"],colors:["애쉬브라운","블루블랙","밀크브라운","쿨블루"]},
  네일아트:{moods:["미니멀","귀여운","드라마틱","청순한"],colors:["밀키화이트","시럽핑크","크롬","자석젤"]},
  메이크업:{moods:["맑은","소프트 글램","센치한","또렷한"],colors:["코랄","로즈","피치","쿨핑크"]},
  포토:{moods:["자연스러운","센치한","도시적인","빈티지"],colors:["필름톤","저채도","흑백","따뜻한 자연광"]},
  웨딩:{moods:["우아한","청순한","로맨틱","클래식"],colors:["피치","로즈","코랄","뉴트럴"]},
  반영구시술:{moods:["자연스러운","또렷한","부드러운","깔끔한"],colors:["내추럴 브라운","애쉬브라운","로즈 립","코랄 립"]}
};

const STORE = {
  posts:"findy2_web_posts",
  likes:"findy2_web_likes",
  saves:"findy2_web_saves",
  preferences:"findy2_web_preferences",
  searches:"findy2_web_searches",
  profile:"findy2_web_profile"
};

const state = {
  route:"home", communityType:"전체", communityCategory:"전체", communitySort:"popular",
  snapCategory:"전체", preferenceCategory:"헤어", selectedPost:null, videoIndex:0
};

const $ = (selector, root=document) => root.querySelector(selector);
const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
const read = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));
const userPosts = () => read(STORE.posts, []);
const allPosts = () => [...userPosts(), ...SEED_POSTS];
const likedIds = () => read(STORE.likes, []);
const savedIds = () => read(STORE.saves, []);
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[char]));

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.classList.remove("show"), 2400);
}

function routeTo(route, push=true) {
  if (!document.querySelector(`[data-view="${route}"]`)) route = "home";
  state.route = route;
  $$(".view").forEach(view => view.classList.toggle("active", view.dataset.view === route));
  $$("[data-route]").forEach(button => button.classList.toggle("active", button.dataset.route === route));
  if (push) history.pushState({route}, "", `#${route}`);
  $("#top-nav").classList.remove("open");
  if (route === "community") renderCommunity();
  if (route === "snap") renderSnaps();
  if (route === "my") renderMyPage();
  if (route === "my-findy") renderPreferenceForm();
  if (route === "search") renderRecentSearches();
  window.scrollTo({top:0,behavior:push ? "smooth" : "auto"});
}

function populateSelects() {
  const options = CATEGORIES.map(category => `<option value="${category}">${category}</option>`).join("");
  $("#community-category").innerHTML = options;
  $("#write-category").innerHTML = CATEGORIES.slice(1).map(category => `<option>${category}</option>`).join("");
}

function postCard(post, compact=false) {
  const isLiked = likedIds().includes(post.id);
  const likes = post.likes + (isLiked ? 1 : 0);
  return `<button class="${compact ? "community-card" : "post-card"}" type="button" data-post-id="${esc(post.id)}">
    <span class="tag">${esc(post.type)}</span>
    <h${compact ? "2" : "3"}>${esc(post.title)}</h${compact ? "2" : "3"}>
    <p>${esc(post.content)}</p>
    <div class="post-meta"><span class="post-author">${esc(post.author)} · ${esc(post.category)}</span><span>좋아요 ${likes} · 댓글 ${post.comments}</span></div>
  </button>`;
}

function snapCard(snap) {
  const saved = savedIds().includes(snap.id);
  return `<button class="snap-card" type="button" data-snap-id="${snap.id}" style="--snap-a:${snap.a};--snap-b:${snap.b}">
    <div><span class="tag">${esc(snap.category)}</span><h3>${esc(snap.title)}</h3><p>${saved ? "저장됨 · " : ""}좋아요 ${snap.likes}</p></div>
  </button>`;
}

function renderHome() {
  $("#home-categories").innerHTML = CATEGORIES.slice(1).map(category => {
    const info = CATEGORY_INFO[category];
    return `<button class="category-card" type="button" data-home-category="${category}">
      <b>${category}</b><span>${info[0]}</span><small>콘텐츠 보기 →</small>
    </button>`;
  }).join("");
  $("#home-popular").innerHTML = [...allPosts()].sort((a,b) => b.likes-a.likes).slice(0,3).map(post => postCard(post)).join("");
  $("#home-snaps").innerHTML = SNAPS.slice(0,4).map(snapCard).join("");
}

function renderCommunity() {
  let posts = allPosts().filter(post =>
    (state.communityType === "전체" || post.type === state.communityType) &&
    (state.communityCategory === "전체" || post.category === state.communityCategory)
  );
  const key = state.communitySort === "latest" ? "date" : state.communitySort === "comments" ? "comments" : "likes";
  posts.sort((a,b) => key === "date" ? b.date.localeCompare(a.date) : b[key]-a[key]);
  $("#community-feed").innerHTML = posts.length ? posts.map(post => postCard(post,true)).join("") : `<div class="aside-card"><h2>아직 글이 없어요.</h2><p>이 분야의 첫 글을 작성해보세요.</p></div>`;
}

function renderSnaps() {
  $("#snap-filters").innerHTML = CATEGORIES.map(category => `<button type="button" class="${state.snapCategory===category?"active":""}" data-snap-filter="${category}">${category}</button>`).join("");
  const list = SNAPS.filter(snap => state.snapCategory === "전체" || snap.category === state.snapCategory);
  $("#snap-feed").innerHTML = list.map(snapCard).join("");
}

function renderVideo() {
  const video = VIDEOS[state.videoIndex];
  $("#video-category").textContent = video.category;
  $("#video-title").textContent = video.title;
  $("#video-likes").textContent = video.likes.toLocaleString();
  $("#video-description").textContent = video.description;
  $(".video-copy p").childNodes[0].nodeValue = `${video.author} · 좋아요 `;
  $("#video-card").style.background = `radial-gradient(circle at 65% 30%,rgba(255,255,255,.22),transparent 24%),linear-gradient(150deg,${video.a},${video.b} 62%)`;
  $("#video-like").classList.toggle("active", likedIds().includes(`video-${state.videoIndex}`));
  $("#video-save").classList.toggle("active", savedIds().includes(`video-${state.videoIndex}`));
}

function renderMyPage() {
  const posts = userPosts();
  const likes = likedIds();
  const saves = savedIds();
  const preferences = read(STORE.preferences, {});
  $("#my-post-count").textContent = posts.length;
  $("#my-like-count").textContent = likes.length;
  $("#my-save-count").textContent = saves.length;
  $("#my-preference-count").textContent = Object.keys(preferences).length;
  const activities = [
    ...posts.map(post => ({title:post.title,meta:`${post.type} · ${post.category}`})),
    ...Object.entries(preferences).map(([category,value]) => ({title:`${category} 취향 저장`,meta:value.mood || "나의 FINDY"}))
  ].slice(0,6);
  $("#my-activity").innerHTML = activities.length
    ? activities.map(item => `<div class="activity-item"><b>${esc(item.title)}</b><span>${esc(item.meta)}</span></div>`).join("")
    : `<div class="aside-card"><h2>아직 활동이 없어요.</h2><p>글을 쓰거나 나의 FINDY를 저장하면 여기에 표시됩니다.</p></div>`;
}

function renderPreferenceForm() {
  $("#preference-tabs").innerHTML = CATEGORIES.slice(1).map(category => `<button type="button" class="${state.preferenceCategory===category?"active":""}" data-preference-category="${category}">${category}</button>`).join("");
  const data = PREFERENCE_DATA[state.preferenceCategory];
  const saved = read(STORE.preferences, {})[state.preferenceCategory] || {};
  $("#preference-mood").value = saved.mood || "";
  $("#preference-color").value = saved.color || "";
  $("#preference-purpose").value = saved.purpose || "";
  $("#mood-suggestions").innerHTML = data.moods.map(value => `<button type="button" data-suggestion-target="preference-mood">${value}</button>`).join("");
  $("#color-suggestions").innerHTML = data.colors.map(value => `<button type="button" data-suggestion-target="preference-color">${value}</button>`).join("");
}

function openWriteModal(mode) {
  $("#write-modal").hidden = false;
  document.body.style.overflow = "hidden";
  if (mode) $("#write-type").value = mode;
  setTimeout(() => $("#write-title-input").focus(), 50);
}

function closeModals() {
  $$(".modal-backdrop").forEach(modal => modal.hidden = true);
  document.body.style.overflow = "";
}

function openPost(id) {
  const post = allPosts().find(item => item.id === id);
  if (!post) return;
  state.selectedPost = post;
  $("#detail-tag").textContent = post.type;
  $("#detail-title").textContent = post.title;
  $("#detail-meta").textContent = `${post.author} · ${post.category} · ${post.date}`;
  $("#detail-content").textContent = post.content;
  $("#detail-like").classList.toggle("active", likedIds().includes(id));
  $("#detail-save").classList.toggle("active", savedIds().includes(id));
  $("#detail-like").textContent = `좋아요 ${post.likes + (likedIds().includes(id) ? 1 : 0)}`;
  $("#detail-save").textContent = savedIds().includes(id) ? "저장됨" : "저장";
  $("#detail-comment").textContent = `댓글 ${post.comments}`;
  $("#detail-modal").hidden = false;
  document.body.style.overflow = "hidden";
}

function toggleCollection(key, id) {
  const list = read(key, []);
  const next = list.includes(id) ? list.filter(item => item !== id) : [...list,id];
  write(key,next);
  return next.includes(id);
}

function performSearch(query) {
  const clean = query.trim();
  if (!clean) return;
  const recent = [clean,...read(STORE.searches,[]).filter(item => item!==clean)].slice(0,6);
  write(STORE.searches,recent);
  $("#search-input").value = clean;
  const needle = clean.toLowerCase();
  const posts = allPosts().filter(post => [post.title,post.content,post.type,post.category].join(" ").toLowerCase().includes(needle));
  const snaps = SNAPS.filter(snap => [snap.title,snap.category].join(" ").toLowerCase().includes(needle));
  $("#search-results").innerHTML = `<div class="section-heading"><div><h2>“${esc(clean)}” 검색 결과</h2><p>게시글 ${posts.length}개 · 스냅 ${snaps.length}개</p></div></div>
    ${posts.map(post => postCard(post,true)).join("")}
    ${snaps.length ? `<div class="snap-grid compact">${snaps.map(snapCard).join("")}</div>` : ""}
    ${!posts.length&&!snaps.length ? `<div class="aside-card"><h2>검색 결과가 없어요.</h2><p>헤어, 네일아트, 메이크업 같은 분야명으로 다시 검색해보세요.</p></div>` : ""}`;
  renderRecentSearches();
}

function renderRecentSearches() {
  const recent = read(STORE.searches,[]);
  $("#recent-searches").innerHTML = recent.length ? `<span>최근 검색</span>${recent.map(item => `<button type="button" data-recent-search="${esc(item)}">${esc(item)}</button>`).join("")}<button type="button" data-clear-searches>전체 삭제</button>` : "";
}

document.addEventListener("click", event => {
  const routeButton = event.target.closest("[data-route]");
  if (routeButton) { event.preventDefault(); routeTo(routeButton.dataset.route); return; }
  if (event.target.closest("#mobile-menu")) { $("#top-nav").classList.toggle("open"); return; }
  if (event.target.closest("#search-open")) { routeTo("search"); setTimeout(() => $("#search-input").focus(),100); return; }
  if (event.target.closest("#write-open") || event.target.closest("#aside-write")) { openWriteModal(); return; }
  const modeButton = event.target.closest("[data-write-mode]");
  if (modeButton) { openWriteModal(modeButton.dataset.writeMode); return; }
  if (event.target.closest("[data-modal-close]") || event.target.classList.contains("modal-backdrop")) { closeModals(); return; }
  const categoryButton = event.target.closest("[data-home-category]");
  if (categoryButton) { state.communityCategory=categoryButton.dataset.homeCategory; $("#community-category").value=state.communityCategory; routeTo("community"); return; }
  const postButton = event.target.closest("[data-post-id]");
  if (postButton) { openPost(postButton.dataset.postId); return; }
  const snap = event.target.closest("[data-snap-id]");
  if (snap) { const active=toggleCollection(STORE.saves,snap.dataset.snapId); toast(active?"스냅을 저장했어요.":"스냅 저장을 해제했어요."); renderSnaps(); renderHome(); return; }
  const typeButton = event.target.closest("[data-type]");
  if (typeButton) { state.communityType=typeButton.dataset.type; $$("#community-type button").forEach(btn=>btn.classList.toggle("active",btn===typeButton)); renderCommunity(); return; }
  const snapFilter = event.target.closest("[data-snap-filter]");
  if (snapFilter) { state.snapCategory=snapFilter.dataset.snapFilter; renderSnaps(); return; }
  const preferenceTab = event.target.closest("[data-preference-category]");
  if (preferenceTab) { state.preferenceCategory=preferenceTab.dataset.preferenceCategory; renderPreferenceForm(); return; }
  const suggestion = event.target.closest("[data-suggestion-target]");
  if (suggestion) {
    const input = $(`#${suggestion.dataset.suggestionTarget}`);
    const values = input.value.split(",").map(value=>value.trim()).filter(Boolean);
    if (!values.includes(suggestion.textContent)) values.push(suggestion.textContent);
    input.value = values.join(", ");
    suggestion.classList.add("active");
    return;
  }
  const recent = event.target.closest("[data-recent-search]");
  if (recent) { performSearch(recent.dataset.recentSearch); return; }
  if (event.target.closest("[data-clear-searches]")) { write(STORE.searches,[]); renderRecentSearches(); return; }
  const myAction = event.target.closest("[data-my-action]");
  if (myAction) {
    const messages={posts:"내가 쓴 글은 최근 활동에서 확인할 수 있어요.",likes:"좋아요한 콘텐츠 모아보기는 곧 연결될 예정이에요.",saves:"저장한 콘텐츠 모아보기는 곧 연결될 예정이에요.",settings:"세부 설정 화면은 곧 연결될 예정이에요.",reservation:"예약 기능은 FINDY 본서비스에서 제공할 예정이에요."};
    toast(messages[myAction.dataset.myAction]); return;
  }
});

$("#community-category").addEventListener("change", event => { state.communityCategory=event.target.value; renderCommunity(); });
$("#community-sort").addEventListener("change", event => { state.communitySort=event.target.value; renderCommunity(); });
$("#hero-search").addEventListener("submit", event => { event.preventDefault(); routeTo("search"); performSearch($("#hero-search-input").value); });
$("#search-form").addEventListener("submit", event => { event.preventDefault(); performSearch($("#search-input").value); });

$("#write-form").addEventListener("submit", event => {
  event.preventDefault();
  const title=$("#write-title-input").value.trim(), content=$("#write-content").value.trim();
  if (title.length<3 || content.length<10) { toast("제목 3자, 내용 10자 이상 입력해주세요."); return; }
  const post={id:`user-${Date.now()}`,type:$("#write-type").value,category:$("#write-category").value,title,content,author:"FINDY 회원",likes:0,saves:0,comments:0,date:new Date().toISOString().slice(0,10)};
  write(STORE.posts,[post,...userPosts()]);
  event.target.reset(); closeModals(); state.communityType="전체"; state.communityCategory="전체"; $("#community-category").value="전체"; renderHome(); routeTo("community"); toast("새 글이 등록되었어요.");
});

$("#preference-form").addEventListener("submit", event => {
  event.preventDefault();
  const preferences=read(STORE.preferences,{});
  preferences[state.preferenceCategory]={mood:$("#preference-mood").value.trim(),color:$("#preference-color").value.trim(),purpose:$("#preference-purpose").value.trim()};
  write(STORE.preferences,preferences); toast(`${state.preferenceCategory} 취향을 저장했어요.`); renderMyPage();
});

$("#detail-like").addEventListener("click", () => {
  if (!state.selectedPost) return;
  const active=toggleCollection(STORE.likes,state.selectedPost.id); openPost(state.selectedPost.id); toast(active?"좋아요를 눌렀어요.":"좋아요를 취소했어요.");
});
$("#detail-save").addEventListener("click", () => {
  if (!state.selectedPost) return;
  const active=toggleCollection(STORE.saves,state.selectedPost.id); openPost(state.selectedPost.id); toast(active?"콘텐츠를 저장했어요.":"저장을 해제했어요.");
});
$("#detail-comment").addEventListener("click", () => toast("댓글 작성 기능은 다음 버전에서 연결할 예정이에요."));
$("#video-next").addEventListener("click", () => { state.videoIndex=(state.videoIndex+1)%VIDEOS.length; renderVideo(); });
$("#video-like").addEventListener("click", () => { toggleCollection(STORE.likes,`video-${state.videoIndex}`); renderVideo(); });
$("#video-save").addEventListener("click", () => { toggleCollection(STORE.saves,`video-${state.videoIndex}`); renderVideo(); });
$("#video-share").addEventListener("click", async () => {
  const title=VIDEOS[state.videoIndex].title;
  try { await navigator.clipboard.writeText(`${title} — FINDY2`); toast("공유 문구를 복사했어요."); } catch { toast("공유 기능은 지원되는 브라우저에서 사용할 수 있어요."); }
});
$("#profile-edit").addEventListener("click", () => toast("프로필 편집 화면은 곧 연결될 예정이에요."));

window.addEventListener("popstate", event => routeTo(event.state?.route || location.hash.slice(1) || "home",false));
window.addEventListener("keydown", event => { if (event.key==="Escape") closeModals(); });

populateSelects();
renderHome();
renderCommunity();
renderSnaps();
renderVideo();
renderPreferenceForm();
renderMyPage();
routeTo(location.hash.slice(1)||"home",false);
