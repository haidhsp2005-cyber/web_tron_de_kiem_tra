// Frontend Logic for Exam Shuffler with Advanced Question Editor & HTML/Code Protection

let currentSessionId = null;
let currentExamData = null;
let currentFilename = "";
let currentActivePart = "part1"; // 'part1', 'part2', 'part3', 'part4', 'all'
let modalState = {
    activePart: "part1",
    qIndex: 0,
    lastFocusedInput: null
};

// Math and Science Symbols Palette Configuration
const SYMBOL_PALETTES = {
    math: [
        { label: "a/b", insert: "\\frac{a}{b}" },
        { label: "√x", insert: "\\sqrt{x}" },
        { label: "³√x", insert: "\\sqrt[3]{x}" },
        { label: "ⁿ√x", insert: "\\sqrt[n]{x}" },
        { label: "x²", insert: "^{2}" },
        { label: "xⁿ", insert: "^{n}" },
        { label: "x₁", insert: "_{1}" },
        { label: "u⃗", insert: "\\vec{u}" },
        { label: "a⃗", insert: "\\vec{a}" },
        { label: "AB⃗", insert: "\\vec{AB}" },
        { label: "∫", insert: "\\int_{a}^{b} f(x)dx" },
        { label: "lim", insert: "\\lim_{x \\to x_0}" },
        { label: "{ x y", insert: "\\begin{cases} x \\\\ y \\end{cases}" },
        { label: "f'(x)", insert: "f'(x)" },
        { label: "°", insert: "^{\\circ}" },
        { label: "Δ", insert: "\\Delta" },
        { label: "π", insert: "\\pi" },
        { label: "α", insert: "\\alpha" },
        { label: "β", insert: "\\beta" },
        { label: "<", insert: "<" },
        { label: ">", insert: ">" },
        { label: "≠", insert: "\\neq" },
        { label: "≈", insert: "\\approx" },
        { label: "±", insert: "\\pm" },
        { label: "∈", insert: "\\in" },
        { label: "∉", insert: "\\notin" },
        { label: "⊂", insert: "\\subset" },
        { label: "∪", insert: "\\cup" },
        { label: "∩", insert: "\\cap" }
    ],
    physics: [
        { label: "λ", insert: "\\lambda" },
        { label: "ω", insert: "\\omega" },
        { label: "φ", insert: "\\varphi" },
        { label: "Ω", insert: "\\Omega" },
        { label: "μ", insert: "\\mu" },
        { label: "ρ", insert: "\\rho" },
        { label: "v⃗", insert: "\\vec{v}" },
        { label: "F⃗", insert: "\\vec{F}" },
        { label: "E⃗", insert: "\\vec{E}" },
        { label: "B⃗", insert: "\\vec{B}" },
        { label: "Δt", insert: "\\Delta t" },
        { label: "10⁻⁶", insert: "10^{-6}" }
    ],
    chem: [
        { label: "H₂O", insert: "H_{2}O" },
        { label: "CO₂", insert: "CO_{2}" },
        { label: "H₂SO₄", insert: "H_{2}SO_{4}" },
        { label: "→", insert: "\\rightarrow" },
        { label: "⇄", insert: "\\rightleftharpoons" },
        { label: "↑", insert: "\\uparrow" },
        { label: "↓", insert: "\\downarrow" },
        { label: "t°", insert: "t^{\\circ}" },
        { label: "Fe³⁺", insert: "Fe^{3+}" },
        { label: "SO₄²⁻", insert: "SO_{4}^{2-}" }
    ]
};

document.addEventListener("DOMContentLoaded", () => {
    initEvents();
    renderSymbolPalette("math");
});

function showToast(message, isSuccess = true) {
    const toast = document.getElementById("toast");
    const msgEl = document.getElementById("toast-message");
    const iconEl = document.getElementById("toast-icon");
    const bodyEl = document.getElementById("toast-body");
    
    if (msgEl) msgEl.textContent = message;
    if (bodyEl) {
        bodyEl.className = isSuccess 
            ? "bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-xl flex items-center space-x-3 text-sm font-semibold border border-emerald-500/40"
            : "bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-xl flex items-center space-x-3 text-sm font-semibold border border-rose-500/40";
    }
    if (iconEl) {
        iconEl.setAttribute("data-lucide", isSuccess ? "check-circle" : "alert-triangle");
        iconEl.className = isSuccess ? "w-5 h-5 text-emerald-400" : "w-5 h-5 text-rose-400";
        lucide.createIcons();
    }

    toast.classList.remove("translate-y-24", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");

    setTimeout(() => {
        toast.classList.remove("translate-y-0", "opacity-100");
        toast.classList.add("translate-y-24", "opacity-0");
    }, 3500);
}

function initEvents() {
    // Step Tab switching
    const btnTab1 = document.getElementById("tab-btn-step1");
    const btnTab2 = document.getElementById("tab-btn-step2");
    const sec1 = document.getElementById("step1-content");
    const sec2 = document.getElementById("step2-content");

    function switchToTab(step) {
        if (step === 1) {
            btnTab1.className = "pb-3 text-sm font-bold border-b-2 border-brand-600 text-brand-700 flex items-center space-x-2";
            btnTab2.className = "pb-3 text-sm font-semibold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center space-x-2";
            sec1.classList.remove("hidden");
            sec2.classList.add("hidden");
        } else {
            btnTab2.className = "pb-3 text-sm font-bold border-b-2 border-brand-600 text-brand-700 flex items-center space-x-2";
            btnTab1.className = "pb-3 text-sm font-semibold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center space-x-2";
            sec2.classList.remove("hidden");
            sec1.classList.add("hidden");
        }
    }

    btnTab1.addEventListener("click", () => switchToTab(1));
    btnTab2.addEventListener("click", () => switchToTab(2));
    document.getElementById("btn-go-to-step2").addEventListener("click", () => switchToTab(2));
    document.getElementById("btn-back-to-step1").addEventListener("click", () => switchToTab(1));

    // Drag and Drop Upload
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");

    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("border-brand-600", "bg-brand-50/20");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("border-brand-600", "bg-brand-50/20");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("border-brand-600", "bg-brand-50/20");
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Subject dropdown
    const subjectSelect = document.getElementById("cfg-subject-select");
    const subjectOther = document.getElementById("cfg-subject-other");
    if (subjectSelect && subjectOther) {
        subjectSelect.addEventListener("change", (e) => {
            if (e.target.value === "__other__") {
                subjectOther.classList.remove("hidden");
                subjectOther.focus();
            } else {
                subjectOther.classList.add("hidden");
            }
        });
    }

    // Load sample exam button
    const btnLoadSample = document.getElementById("btn-load-sample");
    if (btnLoadSample) {
        btnLoadSample.addEventListener("click", () => {
            loadSampleExam();
        });
    }

    // Save Exam
    document.getElementById("btn-save-exam").addEventListener("click", () => {
        saveExamData();
    });
    const btnQuickSave = document.getElementById("btn-sidebar-quick-save");
    if (btnQuickSave) {
        btnQuickSave.addEventListener("click", () => {
            saveExamData();
        });
    }

    // Execute Shuffle
    document.getElementById("btn-execute-shuffle").addEventListener("click", () => {
        executeShuffle();
    });

    // Section Selector Tabs
    document.querySelectorAll(".section-tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const part = btn.dataset.part;
            switchSectionTab(part);
        });
    });

    // Open first question in editor
    const btnOpenFirst = document.getElementById("btn-open-first-editor");
    if (btnOpenFirst) {
        btnOpenFirst.addEventListener("click", () => {
            if (!currentExamData) return;
            const targetPart = (currentExamData[currentActivePart] && currentExamData[currentActivePart].length > 0) 
                ? currentActivePart 
                : ["part1", "part2", "part3", "part4"].find(p => currentExamData[p] && currentExamData[p].length > 0) || "part1";
            openEditModal(targetPart, 0);
        });
    }

    // Modal Events
    initModalEvents();
}

// Upload file to server
async function handleFileUpload(file) {
    const spinner = document.getElementById("loading-spinner");
    const dropzone = document.getElementById("dropzone");
    const statsContainer = document.getElementById("exam-stats-container");

    spinner.classList.remove("hidden");
    dropzone.classList.add("hidden");
    statsContainer.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Lỗi khi tải file lên");
        }

        currentSessionId = data.session_id;
        currentFilename = data.filename;
        currentExamData = data.exam_data;

        renderExamEditor(currentExamData, currentFilename);
        showToast(`Đã đọc thành công file: ${currentFilename}!`, true);
    } catch (err) {
        showToast(err.message, false);
        dropzone.classList.remove("hidden");
    } finally {
        spinner.classList.add("hidden");
    }
}

// Load sample exam directly
async function loadSampleExam() {
    const spinner = document.getElementById("loading-spinner");
    const dropzone = document.getElementById("dropzone");
    const statsContainer = document.getElementById("exam-stats-container");

    spinner.classList.remove("hidden");
    dropzone.classList.add("hidden");
    statsContainer.classList.add("hidden");

    try {
        const response = await fetch("/api/load-sample");
        const data = await response.json();
        
        currentSessionId = data.session_id;
        currentFilename = data.filename;
        currentExamData = data.exam_data;

        renderExamEditor(currentExamData, currentFilename);
        showToast("Đã nạp thành công Đề thi mẫu môn Toán (in đậm đáp án đỏ)!", true);
    } catch (err) {
        showToast("Không thể tải đề mẫu: " + err.message, false);
        dropzone.classList.remove("hidden");
    } finally {
        spinner.classList.add("hidden");
    }
}

// Switch between Section Tabs in Question Editor (Part 1, 2, 3, 4, All)
function switchSectionTab(partKey) {
    currentActivePart = partKey;

    document.querySelectorAll(".section-tab-btn").forEach(b => {
        const p = b.dataset.part;
        if (p === partKey) {
            b.className = "section-tab-btn active px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 bg-blue-900 text-white shadow-sm";
        } else {
            let bgClass = "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50";
            if (p === "part1") bgClass = "bg-blue-50 text-blue-800 border border-blue-200 hover:bg-blue-100";
            if (p === "part2") bgClass = "bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100";
            if (p === "part3") bgClass = "bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100";
            if (p === "part4") bgClass = "bg-purple-50 text-purple-800 border border-purple-200 hover:bg-purple-100";
            b.className = `section-tab-btn px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${bgClass}`;
        }
    });

    const p1View = document.getElementById("p1-section-view");
    const p2View = document.getElementById("p2-section-view");
    const p3View = document.getElementById("p3-section-view");
    const p4View = document.getElementById("p4-section-view");
    const bannerText = document.getElementById("section-instruction-text");
    const bannerPill = document.getElementById("section-banner-pill");

    if (partKey === "all") {
        p1View.classList.remove("hidden");
        p2View.classList.remove("hidden");
        p3View.classList.remove("hidden");
        p4View.classList.remove("hidden");
        if (bannerText) {
            bannerText.innerHTML = "<strong>Xem tất cả:</strong> Toàn bộ 4 phần của đề thi. Nhấp vào chữ cái để đổi đáp án nhanh, hoặc bấm <span class='inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-indigo-600 text-white'>✏️ Sửa câu này</span> để mở khung chỉnh sửa chi tiết.";
        }
        const total = (currentExamData.part1?.length || 0) + (currentExamData.part2?.length || 0) + (currentExamData.part3?.length || 0) + (currentExamData.part4?.length || 0);
        if (bannerPill) bannerPill.textContent = `${total} câu`;
    } else {
        p1View.classList.toggle("hidden", partKey !== "part1");
        p2View.classList.toggle("hidden", partKey !== "part2");
        p3View.classList.toggle("hidden", partKey !== "part3");
        p4View.classList.toggle("hidden", partKey !== "part4");

        const count = currentExamData[partKey] ? currentExamData[partKey].length : 0;
        if (bannerPill) bannerPill.textContent = `${count} câu`;

        if (partKey === "part1" && bannerText) {
            bannerText.innerHTML = `<strong>Phần I (${(count * 0.25).toFixed(1)} điểm):</strong> Trắc nghiệm 4 lựa chọn. Nhấp vào chữ cái để chọn đáp án đúng. Bấm <span class='inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-indigo-600 text-white'>✏️ Sửa câu này</span> để mở khung chỉnh sửa chi tiết.`;
        } else if (partKey === "part2" && bannerText) {
            bannerText.innerHTML = `<strong>Phần II (${count * 1.0} điểm):</strong> Trắc nghiệm Đúng / Sai. Bấm nút <strong>Đúng</strong> hoặc <strong>Sai</strong> cho mỗi ý a, b, c, d. Bấm <span class='inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-indigo-600 text-white'>✏️ Sửa câu này</span> để sửa lệnh hỏi.`;
        } else if (partKey === "part3" && bannerText) {
            bannerText.innerHTML = `<strong>Phần III:</strong> Câu hỏi trắc nghiệm trả lời ngắn (Điền số / kết quả). Bấm <span class='inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-indigo-600 text-white'>✏️ Sửa câu này</span> để chỉnh sửa nội dung hoặc đáp số.`;
        } else if (partKey === "part4" && bannerText) {
            bannerText.innerHTML = `<strong>Phần IV:</strong> Câu hỏi Tự luận kèm hướng dẫn chấm & thang điểm. Bấm <span class='inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-indigo-600 text-white'>✏️ Sửa câu này</span> để biên tập chi tiết.`;
        }
    }

    renderNavigatorSidebar();
}

// Render questions into Step 1
function renderExamEditor(data, filename) {
    const dropzone = document.getElementById("dropzone");
    const statsContainer = document.getElementById("exam-stats-container");

    dropzone.classList.remove("hidden");
    statsContainer.classList.remove("hidden");

    // Metadata
    document.getElementById("badge-filename").textContent = filename;
    document.getElementById("exam-title-text").textContent = data.metadata.title || "Đề Kiểm Tra";
    document.getElementById("exam-meta-text").textContent = `Môn: ${data.metadata.subject || 'Khoa học Tự nhiên'} | Thời gian: ${data.metadata.time || '90 phút'} | Năm học: ${data.metadata.year || '2026 - 2027'}`;

    // Fill config inputs
    const schoolInput = document.getElementById("cfg-school");
    if (schoolInput) schoolInput.value = data.metadata.school || "THPT Long Cang";
    const yearInput = document.getElementById("cfg-year");
    if (yearInput) yearInput.value = data.metadata.year || "2026 - 2027";
    if (data.metadata.time) document.getElementById("cfg-time").value = data.metadata.time;

    // Set Subject select
    const subSelect = document.getElementById("cfg-subject-select");
    const subOther = document.getElementById("cfg-subject-other");
    if (subSelect && subOther) {
        const parsedSub = (data.metadata.subject || '').trim();
        let matched = false;
        for (let i = 0; i < subSelect.options.length; i++) {
            const optVal = subSelect.options[i].value;
            if (optVal !== '__other__' && parsedSub && (parsedSub.toLowerCase().includes(optVal.toLowerCase()) || optVal.toLowerCase().includes(parsedSub.toLowerCase()))) {
                subSelect.value = optVal;
                subOther.classList.add("hidden");
                matched = true;
                break;
            }
        }
        if (!matched && parsedSub) {
            subSelect.value = '__other__';
            subOther.classList.remove("hidden");
            subOther.value = parsedSub;
        } else if (!matched) {
            subSelect.value = 'Toán';
            subOther.classList.add("hidden");
        }
    }

    // Counts
    const p1Count = data.part1 ? data.part1.length : 0;
    const p2Count = data.part2 ? data.part2.length : 0;
    const p3Count = data.part3 ? data.part3.length : 0;
    const p4Count = data.part4 ? data.part4.length : 0;
    const totalCount = p1Count + p2Count + p3Count + p4Count;

    document.getElementById("tab-p1-count").textContent = p1Count;
    document.getElementById("tab-p2-count").textContent = p2Count;
    document.getElementById("tab-p3-count").textContent = p3Count;
    document.getElementById("tab-p4-count").textContent = p4Count;
    document.getElementById("tab-all-count").textContent = `${totalCount} câu`;
    document.getElementById("sidebar-total-badge").textContent = `${totalCount} câu`;

    // 1. Render Part I Questions (Matching Screenshot 1)
    const p1Container = document.getElementById("p1-questions-list");
    p1Container.innerHTML = "";
    if (data.part1) {
        data.part1.forEach((q, idx) => {
            const card = document.createElement("div");
            card.id = `card-part1-${idx}`;
            card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3.5 transition hover:shadow-md";

            card.innerHTML = `
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 rounded-lg bg-blue-600 text-white font-bold text-xs shadow-xs">Câu ${idx + 1}</span>
                        <span class="px-2 py-0.5 rounded-md text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">TNKQ (0.25đ)</span>
                        ${q.has_red ? `
                            <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                                <span class="w-1.5 h-1.5 rounded-full bg-rose-600 inline-block"></span>
                                <span>Đáp án: ${q.correct}</span>
                            </span>
                        ` : ''}
                    </div>

                    <div class="flex items-center space-x-2">
                        <button type="button" class="btn-edit-question px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition flex items-center space-x-1.5 cursor-pointer" data-part="part1" data-idx="${idx}">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            <span>Sửa câu này</span>
                        </button>
                        <button type="button" class="btn-delete-question w-7 h-7 rounded-full text-slate-400 hover:text-rose-600 hover:bg-rose-50 flex items-center justify-center transition cursor-pointer" data-part="part1" data-idx="${idx}" title="Xóa câu này">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>

                <!-- Question Text -->
                <div class="math-preview p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 text-sm text-slate-900 leading-relaxed font-sans shadow-2xs" id="p1-q-view-${idx}">${formatMathPreview(q.question)}</div>

                <!-- 4 Choices Grid (Matching Image 1) -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-1">
                    ${['A', 'B', 'C', 'D'].map(k => {
                        const isCorrect = (q.correct === k);
                        return `
                            <div class="choice-math-card cursor-pointer p-3 rounded-xl border transition-all duration-150 ${isCorrect ? 'border-2 border-emerald-500 bg-emerald-50/70 ring-2 ring-emerald-500/20 shadow-xs' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'} flex items-center space-x-2.5" data-qidx="${idx}" data-key="${k}">
                                <div class="w-6 h-6 rounded-full ${isCorrect ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-700'} font-bold text-xs flex items-center justify-center shrink-0">
                                    ${k}
                                </div>
                                <div class="math-preview text-sm ${isCorrect ? 'font-bold text-emerald-950' : 'font-medium text-slate-800'} flex-1 leading-snug" id="p1-c-view-${idx}-${k}">
                                    ${formatMathPreview(q.choices[k] || '')}
                                </div>
                                ${isCorrect ? '<span class="text-emerald-600 font-bold text-sm ml-auto shrink-0">✓</span>' : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
            p1Container.appendChild(card);
        });
    }

    // 2. Render Part II Questions (True / False)
    const p2Container = document.getElementById("p2-questions-list");
    p2Container.innerHTML = "";
    if (data.part2) {
        data.part2.forEach((q, idx) => {
            const card = document.createElement("div");
            card.id = `card-part2-${idx}`;
            card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3.5 transition hover:shadow-md";

            card.innerHTML = `
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-bold text-xs shadow-xs">Câu ${idx + 1}</span>
                        <span class="px-2 py-0.5 rounded-md text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Đúng/Sai (1.0đ)</span>
                    </div>

                    <div class="flex items-center space-x-2">
                        <button type="button" class="btn-edit-question px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition flex items-center space-x-1.5 cursor-pointer" data-part="part2" data-idx="${idx}">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            <span>Sửa câu này</span>
                        </button>
                        <button type="button" class="btn-delete-question w-7 h-7 rounded-full text-slate-400 hover:text-rose-600 hover:bg-rose-50 flex items-center justify-center transition cursor-pointer" data-part="part2" data-idx="${idx}" title="Xóa câu này">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>

                <!-- Question Text -->
                <div class="math-preview p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 text-sm text-slate-900 leading-relaxed font-sans shadow-2xs" id="p2-q-view-${idx}">${formatMathPreview(q.question)}</div>

                <!-- 4 Items (a, b, c, d) -->
                <div class="space-y-2 pt-1">
                    ${['a', 'b', 'c', 'd'].map(k => {
                        const item = q.items[k] || { text: '', correct: false };
                        const isTrue = item.correct;
                        return `
                            <div class="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between gap-3 shadow-2xs">
                                <div class="flex items-center space-x-2.5 flex-1">
                                    <span class="font-bold text-xs text-slate-700 w-5">${k})</span>
                                    <div class="math-preview text-sm font-medium text-slate-800" id="p2-item-view-${idx}-${k}">${formatMathPreview(item.text || '')}</div>
                                </div>
                                <div class="flex items-center space-x-1.5 shrink-0">
                                    <button type="button" class="p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-2xs ${isTrue ? 'bg-emerald-600 text-white shadow-emerald-500/20' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}" data-qidx="${idx}" data-key="${k}" data-val="true">
                                        Đúng
                                    </button>
                                    <button type="button" class="p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-2xs ${!isTrue ? 'bg-rose-600 text-white shadow-rose-500/20' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}" data-qidx="${idx}" data-key="${k}" data-val="false">
                                        Sai
                                    </button>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
            p2Container.appendChild(card);
        });
    }

    // 3. Render Part III Questions (Short Answer)
    const p3Container = document.getElementById("p3-questions-list");
    p3Container.innerHTML = "";
    if (data.part3) {
        data.part3.forEach((q, idx) => {
            const card = document.createElement("div");
            card.id = `card-part3-${idx}`;
            card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3.5 transition hover:shadow-md";

            card.innerHTML = `
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 rounded-lg bg-amber-600 text-white font-bold text-xs shadow-xs">Câu ${idx + 1}</span>
                        <span class="px-2 py-0.5 rounded-md text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">TL Ngắn (0.25đ)</span>
                    </div>

                    <div class="flex items-center space-x-2">
                        <button type="button" class="btn-edit-question px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition flex items-center space-x-1.5 cursor-pointer" data-part="part3" data-idx="${idx}">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            <span>Sửa câu này</span>
                        </button>
                        <button type="button" class="btn-delete-question w-7 h-7 rounded-full text-slate-400 hover:text-rose-600 hover:bg-rose-50 flex items-center justify-center transition cursor-pointer" data-part="part3" data-idx="${idx}" title="Xóa câu này">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>

                <div class="math-preview p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 text-sm text-slate-900 leading-relaxed font-sans shadow-2xs" id="p3-q-view-${idx}">${formatMathPreview(q.question)}</div>

                <div class="flex items-center space-x-3 pt-1">
                    <label class="text-xs font-bold text-slate-700">Đáp án:</label>
                    <input type="text" value="${escapeHtml((q.answer || '').replace(/^\$|\$$/g, ''))}" class="p3-ans-text w-36 px-3 py-1.5 text-xs font-bold border border-amber-300 rounded-lg bg-amber-50/50 text-amber-900 outline-none focus:ring-2 focus:ring-amber-500" data-idx="${idx}" placeholder="Nhập đáp số...">
                    <span class="math-preview text-xs font-bold text-amber-800 ml-2" id="p3-prev-ans-${idx}">${formatMathPreview(q.answer || '')}</span>
                </div>
            `;
            p3Container.appendChild(card);
        });
    }

    // 4. Render Part IV Questions (Essay)
    const p4Container = document.getElementById("p4-questions-list");
    p4Container.innerHTML = "";
    if (data.part4) {
        data.part4.forEach((q, idx) => {
            const card = document.createElement("div");
            card.id = `card-part4-${idx}`;
            card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3.5 transition hover:shadow-md";

            card.innerHTML = `
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 rounded-lg bg-purple-600 text-white font-bold text-xs shadow-xs">Câu ${idx + 1}</span>
                        <span class="px-2 py-0.5 rounded-md text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">Tự luận</span>
                    </div>

                    <div class="flex items-center space-x-2">
                        <button type="button" class="btn-edit-question px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition flex items-center space-x-1.5 cursor-pointer" data-part="part4" data-idx="${idx}">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            <span>Sửa câu này</span>
                        </button>
                        <button type="button" class="btn-delete-question w-7 h-7 rounded-full text-slate-400 hover:text-rose-600 hover:bg-rose-50 flex items-center justify-center transition cursor-pointer" data-part="part4" data-idx="${idx}" title="Xóa câu này">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>

                <div class="math-preview p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 text-sm text-slate-900 leading-relaxed font-sans shadow-2xs" id="p4-q-view-${idx}">${formatMathPreview(q.question)}</div>

                ${q.guide ? `
                    <div class="space-y-1 pt-1">
                        <label class="text-xs text-purple-700 font-bold">Hướng dẫn chấm & Thang điểm:</label>
                        <div class="math-preview p-3.5 rounded-xl bg-purple-50/40 border border-purple-200 text-xs text-slate-800 leading-relaxed font-sans shadow-2xs" id="p4-guide-view-${idx}">${formatMathPreview(q.guide)}</div>
                    </div>
                ` : ''}
            `;
            p4Container.appendChild(card);
        });
    }

    // Attach listeners for interactive edits & choices
    attachEditorListeners();

    // Render Question Navigator Sidebar
    renderNavigatorSidebar();

    // Render Lucide icons
    lucide.createIcons();

    // Render KaTeX for all math previews
    renderMathSafe(document.body);
}

// Render the 5-column Navigator Sidebar (Matching Screenshot 1)
function renderNavigatorSidebar() {
    const grid = document.getElementById("sidebar-questions-grid");
    const titleEl = document.getElementById("sidebar-section-title");
    const countEl = document.getElementById("sidebar-section-count");
    if (!grid || !currentExamData) return;

    grid.innerHTML = "";
    
    // Choose which questions to display based on currentActivePart
    let questions = [];
    let partLabel = "PHẦN I (TNKQ)";
    let partKey = currentActivePart;

    if (partKey === "all" || partKey === "part1") {
        questions = currentExamData.part1 || [];
        partLabel = "PHẦN I (TNKQ)";
        partKey = "part1";
    } else if (partKey === "part2") {
        questions = currentExamData.part2 || [];
        partLabel = "PHẦN II (ĐÚNG/SAI)";
    } else if (partKey === "part3") {
        questions = currentExamData.part3 || [];
        partLabel = "PHẦN III (TL NGẮN)";
    } else if (partKey === "part4") {
        questions = currentExamData.part4 || [];
        partLabel = "PHẦN IV (TỰ LUẬN)";
    }

    if (titleEl) titleEl.textContent = partLabel;
    if (countEl) countEl.textContent = `${questions.length} CÂU`;

    questions.forEach((q, idx) => {
        const itemBtn = document.createElement("button");
        itemBtn.type = "button";

        let ansText = "-";
        let hasAns = false;

        if (partKey === "part1") {
            ansText = q.correct || "-";
            hasAns = !!q.correct;
        } else if (partKey === "part2") {
            const trues = Object.values(q.items || {}).filter(it => it.correct).length;
            ansText = `${trues}Đ`;
            hasAns = true;
        } else if (partKey === "part3") {
            ansText = q.answer ? "✓" : "-";
            hasAns = !!q.answer;
        } else if (partKey === "part4") {
            ansText = q.guide ? "✓" : "-";
            hasAns = !!q.guide;
        }

        const isCurrentlyEditing = (modalState.activePart === partKey && modalState.qIndex === idx && !document.getElementById("question-edit-modal").classList.contains("hidden"));

        let styleClass = "border-slate-200 bg-slate-50/50 text-slate-400";
        if (isCurrentlyEditing) {
            styleClass = "border-indigo-500 bg-indigo-50 text-indigo-700 ring-2 ring-indigo-400 shadow-xs";
        } else if (hasAns) {
            styleClass = "border-emerald-300 bg-emerald-50/50 text-slate-800 hover:bg-emerald-100/60";
        }

        itemBtn.className = `p-1.5 rounded-xl border text-center transition cursor-pointer hover:shadow-xs flex flex-col items-center justify-center ${styleClass}`;
        itemBtn.innerHTML = `
            <span class="font-bold text-xs text-slate-800">${idx + 1}</span>
            <span class="font-bold text-xs ${hasAns ? 'text-emerald-700' : 'text-slate-400'}">${ansText}</span>
        `;

        itemBtn.addEventListener("click", () => {
            // Scroll to card smoothly
            const cardEl = document.getElementById(`card-${partKey}-${idx}`);
            if (cardEl) {
                cardEl.scrollIntoView({ behavior: "smooth", block: "center" });
                cardEl.classList.add("ring-2", "ring-indigo-500");
                setTimeout(() => cardEl.classList.remove("ring-2", "ring-indigo-500"), 1200);
            }
            openEditModal(partKey, idx);
        });

        grid.appendChild(itemBtn);
    });
}

function attachEditorListeners() {
    // Clickable choice cards for Part I answers
    document.querySelectorAll(".choice-math-card").forEach(card => {
        card.addEventListener("click", () => {
            const qIdx = parseInt(card.dataset.qidx);
            const key = card.dataset.key;
            currentExamData.part1[qIdx].correct = key;
            currentExamData.part1[qIdx].has_red = true;
            currentExamData.part1[qIdx].is_edited = true;

            const parentGrid = card.closest(".grid");
            if (parentGrid) {
                parentGrid.querySelectorAll(".choice-math-card").forEach(c => {
                    const isSelected = (c.dataset.key === key);
                    c.className = `choice-math-card cursor-pointer p-3 rounded-xl border transition-all duration-150 ${isSelected ? 'border-2 border-emerald-500 bg-emerald-50/70 ring-2 ring-emerald-500/20 shadow-xs' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'} flex items-center space-x-2.5`;
                    const badge = c.querySelector(".w-6.h-6");
                    if (badge) {
                        badge.className = `w-6 h-6 rounded-full ${isSelected ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-700'} font-bold text-xs flex items-center justify-center shrink-0`;
                    }
                    const textEl = c.querySelector(".math-preview");
                    if (textEl) {
                        textEl.className = `math-preview text-sm ${isSelected ? 'font-bold text-emerald-950' : 'font-medium text-slate-800'} flex-1 leading-snug`;
                    }
                    let checkEl = c.querySelector(".text-emerald-600");
                    if (isSelected && !checkEl) {
                        const chk = document.createElement("span");
                        chk.className = "text-emerald-600 font-bold text-sm ml-auto shrink-0";
                        chk.textContent = "✓";
                        c.appendChild(chk);
                    } else if (!isSelected && checkEl) {
                        checkEl.remove();
                    }
                });
            }

            renderNavigatorSidebar();
        });
    });

    // Part II Toggle buttons (True/False)
    document.querySelectorAll(".p2-toggle-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const qIdx = parseInt(btn.dataset.qidx);
            const key = btn.dataset.key;
            const isTrue = (btn.dataset.val === "true");

            currentExamData.part2[qIdx].items[key].correct = isTrue;
            currentExamData.part2[qIdx].is_edited = true;

            const parentDiv = btn.closest(".flex.items-center.space-x-1\\.5");
            if (parentDiv) {
                const btnTrue = parentDiv.querySelector('[data-val="true"]');
                const btnFalse = parentDiv.querySelector('[data-val="false"]');

                if (isTrue) {
                    btnTrue.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-2xs bg-emerald-600 text-white shadow-emerald-500/20";
                    btnFalse.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-2xs bg-slate-100 text-slate-600 hover:bg-slate-200";
                } else {
                    btnTrue.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-2xs bg-slate-100 text-slate-600 hover:bg-slate-200";
                    btnFalse.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-2xs bg-rose-600 text-white shadow-rose-500/20";
                }
            }

            renderNavigatorSidebar();
        });
    });

    // Part III Answer input
    document.querySelectorAll(".p3-ans-text").forEach(input => {
        input.addEventListener("input", (e) => {
            const idx = parseInt(e.target.dataset.idx);
            currentExamData.part3[idx].answer = e.target.value;
            currentExamData.part3[idx].is_edited = true;
            const prev = document.getElementById(`p3-prev-ans-${idx}`);
            if (prev) {
                prev.innerHTML = formatMathPreview(e.target.value);
                renderMathSafe(prev);
            }
            renderNavigatorSidebar();
        });
    });

    // Open Edit Modal buttons
    document.querySelectorAll(".btn-edit-question").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const part = btn.dataset.part;
            const idx = parseInt(btn.dataset.idx);
            openEditModal(part, idx);
        });
    });

    // Delete question buttons
    document.querySelectorAll(".btn-delete-question").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const part = btn.dataset.part;
            const idx = parseInt(btn.dataset.idx);
            if (confirm(`Bạn có chắc chắn muốn xóa Câu ${idx + 1} của ${part.toUpperCase()} không?`)) {
                currentExamData[part].splice(idx, 1);
                renderExamEditor(currentExamData, currentFilename);
                showToast(`Đã xóa câu hỏi thành công!`, true);
            }
        });
    });
}

// -------------------------------------------------------------
// ADVANCED QUESTION EDIT MODAL (Matching Screenshot 2)
// -------------------------------------------------------------

function initModalEvents() {
    const modal = document.getElementById("question-edit-modal");
    const btnClose = document.getElementById("modal-btn-close");
    const btnCancel = document.getElementById("modal-btn-cancel");
    const btnSaveCurrent = document.getElementById("modal-btn-save-current");
    const btnSaveAndNext = document.getElementById("modal-btn-save-and-next");
    const btnPrev = document.getElementById("modal-btn-prev");
    const btnNext = document.getElementById("modal-btn-next");

    function closeModal() {
        modal.classList.add("hidden");
        renderNavigatorSidebar();
    }

    if (btnClose) btnClose.addEventListener("click", closeModal);
    if (btnCancel) btnCancel.addEventListener("click", closeModal);

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        if (modal.classList.contains("hidden")) return;
        if (e.key === "Escape") {
            closeModal();
        } else if (e.ctrlKey && e.key === "Enter") {
            saveModalQuestion(true, false);
        }
    });

    if (btnSaveCurrent) {
        btnSaveCurrent.addEventListener("click", () => {
            saveModalQuestion(true, false);
        });
    }

    if (btnSaveAndNext) {
        btnSaveAndNext.addEventListener("click", () => {
            saveModalQuestion(false, true);
        });
    }

    if (btnPrev) {
        btnPrev.addEventListener("click", () => {
            saveModalQuestion(false, false);
            navigateModal(-1);
        });
    }

    if (btnNext) {
        btnNext.addEventListener("click", () => {
            saveModalQuestion(false, false);
            navigateModal(1);
        });
    }

    // Code indentation buttons
    const qTextarea = document.getElementById("modal-q-text");
    const btnIndent = document.getElementById("btn-indent-code");
    const btnUnindent = document.getElementById("btn-unindent-code");
    const btnFormatPy = document.getElementById("btn-format-python-code");

    if (btnIndent && qTextarea) {
        btnIndent.addEventListener("click", () => indentTextarea(qTextarea, 4));
    }
    if (btnUnindent && qTextarea) {
        btnUnindent.addEventListener("click", () => unindentTextarea(qTextarea, 4));
    }
    if (btnFormatPy && qTextarea) {
        btnFormatPy.addEventListener("click", () => formatPythonIndentation(qTextarea));
    }

    // Support Tab key in question textarea (inserts 4 spaces!)
    if (qTextarea) {
        qTextarea.addEventListener("keydown", (e) => {
            if (e.key === "Tab") {
                e.preventDefault();
                if (e.shiftKey) {
                    unindentTextarea(qTextarea, 4);
                } else {
                    indentTextarea(qTextarea, 4);
                }
            }
        });

        qTextarea.addEventListener("input", updateModalLivePreview);
        qTextarea.addEventListener("focus", () => { modalState.lastFocusedInput = qTextarea; });
    }

    // Modal Image Upload
    const btnModalImg = document.getElementById("btn-modal-upload-image");
    const fileModalImg = document.getElementById("modal-image-file-input");
    if (btnModalImg && fileModalImg) {
        btnModalImg.addEventListener("click", () => fileModalImg.click());
        fileModalImg.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                const reader = new FileReader();
                reader.onload = (re) => {
                    const dataUri = re.target.result;
                    const imgHtml = `\n<div class="exam-image-wrap" style="text-align:center;margin:8px 0;"><img src="${dataUri}" class="exam-figure" style="max-width:100%;max-height:350px;" /></div>\n`;
                    insertAtCursor(qTextarea, imgHtml);
                    updateModalLivePreview();
                };
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }

    // Subject palette tab switching
    document.querySelectorAll(".subject-palette-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".subject-palette-tab").forEach(t => {
                t.className = "subject-palette-tab px-3 py-1 rounded-md font-bold text-xs bg-white text-slate-600 border border-slate-200 hover:bg-slate-100";
            });
            tab.className = "subject-palette-tab active px-3 py-1 rounded-md font-bold text-xs bg-indigo-600 text-white";
            renderSymbolPalette(tab.dataset.subject);
        });
    });

    // Quick Insert Buttons (^2, _1, $ ... $)
    document.querySelectorAll(".quick-insert-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const ins = btn.dataset.insert;
            const target = modalState.lastFocusedInput || qTextarea;
            insertAtCursor(target, ins);
            updateModalLivePreview();
        });
    });
}

function renderSymbolPalette(subjectKey) {
    const paletteContainer = document.getElementById("symbol-buttons-palette");
    if (!paletteContainer) return;
    paletteContainer.innerHTML = "";

    const symbols = SYMBOL_PALETTES[subjectKey] || SYMBOL_PALETTES.math;
    symbols.forEach(sym => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "px-2 py-1 rounded border border-slate-200 bg-white hover:bg-indigo-50 hover:border-indigo-400 font-mono text-xs font-semibold text-slate-700 hover:text-indigo-700 transition shadow-2xs";
        btn.textContent = sym.label;
        btn.title = sym.insert;
        btn.addEventListener("click", () => {
            const qTextarea = document.getElementById("modal-q-text");
            const target = modalState.lastFocusedInput || qTextarea;
            insertAtCursor(target, sym.insert);
            updateModalLivePreview();
        });
        paletteContainer.appendChild(btn);
    });
}

function insertAtCursor(inputEl, textToInsert) {
    if (!inputEl) return;
    const start = inputEl.selectionStart || 0;
    const end = inputEl.selectionEnd || 0;
    const val = inputEl.value;

    if (textToInsert === "$ $") {
        if (start !== end) {
            const selected = val.substring(start, end);
            inputEl.value = val.substring(0, start) + "$" + selected + "$" + val.substring(end);
            inputEl.selectionStart = start;
            inputEl.selectionEnd = end + 2;
        } else {
            inputEl.value = val.substring(0, start) + "$  $" + val.substring(end);
            inputEl.selectionStart = start + 2;
            inputEl.selectionEnd = start + 2;
        }
    } else {
        inputEl.value = val.substring(0, start) + textToInsert + val.substring(end);
        inputEl.selectionStart = start + textToInsert.length;
        inputEl.selectionEnd = start + textToInsert.length;
    }
    inputEl.focus();
}

function indentTextarea(textarea, numSpaces = 4) {
    const spaces = " ".repeat(numSpaces);
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const val = textarea.value;

    if (start === end) {
        textarea.value = val.substring(0, start) + spaces + val.substring(end);
        textarea.selectionStart = textarea.selectionEnd = start + numSpaces;
    } else {
        const lineStart = val.lastIndexOf("\n", start - 1) + 1;
        const lineEnd = val.indexOf("\n", end) === -1 ? val.length : val.indexOf("\n", end);
        const selectedLines = val.substring(lineStart, lineEnd).split("\n");
        const indented = selectedLines.map(l => spaces + l).join("\n");

        textarea.value = val.substring(0, lineStart) + indented + val.substring(lineEnd);
        textarea.selectionStart = start + numSpaces;
        textarea.selectionEnd = end + (numSpaces * selectedLines.length);
    }
    updateModalLivePreview();
}

function unindentTextarea(textarea, numSpaces = 4) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const val = textarea.value;

    const lineStart = val.lastIndexOf("\n", start - 1) + 1;
    const lineEnd = val.indexOf("\n", end) === -1 ? val.length : val.indexOf("\n", end);
    const selectedLines = val.substring(lineStart, lineEnd).split("\n");
    let removedTotal = 0;

    const unindented = selectedLines.map(l => {
        let count = 0;
        while (count < numSpaces && l.startsWith(" ")) {
            l = l.substring(1);
            count++;
        }
        removedTotal += count;
        return l;
    }).join("\n");

    textarea.value = val.substring(0, lineStart) + unindented + val.substring(lineEnd);
    textarea.selectionStart = Math.max(lineStart, start - numSpaces);
    textarea.selectionEnd = Math.max(lineStart, end - removedTotal);
    updateModalLivePreview();
}

function formatPythonIndentation(textarea) {
    let val = textarea.value;
    // Replace tabs with 4 spaces
    val = val.replace(/\t/g, "    ");
    // Trim trailing whitespace per line
    const lines = val.split("\n").map(l => l.replace(/\s+$/, ""));
    textarea.value = lines.join("\n");
    updateModalLivePreview();
    showToast("Đã chuẩn hóa thụt lề 4 dấu cách cho mã nguồn!", true);
}

function openEditModal(partKey, qIndex) {
    if (!currentExamData || !currentExamData[partKey]) return;
    const qList = currentExamData[partKey];
    if (qIndex < 0 || qIndex >= qList.length) return;

    modalState.activePart = partKey;
    modalState.qIndex = qIndex;

    const q = qList[qIndex];
    const modal = document.getElementById("question-edit-modal");

    // Header info
    document.getElementById("modal-title").textContent = `Chỉnh sửa Câu ${qIndex + 1}`;
    
    let partBadgeName = "Phần I - TNKQ 4 lựa chọn";
    if (partKey === "part2") partBadgeName = "Phần II - Đúng / Sai";
    if (partKey === "part3") partBadgeName = "Phần III - Trả lời ngắn";
    if (partKey === "part4") partBadgeName = "Phần IV - Tự luận";
    document.getElementById("modal-part-badge").textContent = partBadgeName;

    document.getElementById("modal-question-indicator").textContent = `${qIndex + 1} / ${qList.length}`;

    // Fill Question Text
    const qTextarea = document.getElementById("modal-q-text");
    qTextarea.value = (q.question || '').replace(/<br\s*\/?>/gi, '\n');
    modalState.lastFocusedInput = qTextarea;

    // Toggle Section Specific Inputs
    const p1ChoicesBox = document.getElementById("modal-part1-choices");
    const p2ItemsBox = document.getElementById("modal-part2-items");
    const p3AnsBox = document.getElementById("modal-part3-answer");
    const p4GuideBox = document.getElementById("modal-part4-guide");

    p1ChoicesBox.classList.toggle("hidden", partKey !== "part1");
    p2ItemsBox.classList.toggle("hidden", partKey !== "part2");
    p3AnsBox.classList.toggle("hidden", partKey !== "part3");
    p4GuideBox.classList.toggle("hidden", partKey !== "part4");

    // Part 1 Choices
    if (partKey === "part1") {
        const choicesContainer = document.getElementById("modal-choices-container");
        choicesContainer.innerHTML = "";
        const correctKey = q.correct || "A";
        document.getElementById("modal-correct-badge").textContent = `Đáp án đúng: ${correctKey}`;

        ['A', 'B', 'C', 'D'].forEach(k => {
            const isCorrect = (correctKey === k);
            const row = document.createElement("div");
            row.className = `p-2.5 rounded-xl border transition flex items-center space-x-3 ${isCorrect ? 'border-2 border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20' : 'border-slate-200 bg-white'}`;
            row.innerHTML = `
                <label class="flex items-center space-x-2 cursor-pointer shrink-0">
                    <input type="radio" name="modal_choice_correct" value="${k}" ${isCorrect ? 'checked' : ''} class="modal-choice-radio text-emerald-600 focus:ring-emerald-500">
                    <span class="w-6 h-6 rounded-full ${isCorrect ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-700'} font-bold text-xs flex items-center justify-center">${k}</span>
                </label>
                <input type="text" class="modal-choice-input flex-1 px-3 py-1.5 text-sm font-medium border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500" data-key="${k}" value="${escapeHtml(q.choices ? q.choices[k] || '' : '')}" placeholder="Nội dung phương án ${k}...">
            `;

            const radio = row.querySelector("input[type='radio']");
            radio.addEventListener("change", () => {
                document.getElementById("modal-correct-badge").textContent = `Đáp án đúng: ${k}`;
                updateModalLivePreview();
                openEditModal(partKey, qIndex); // Re-render styling
            });

            const input = row.querySelector(".modal-choice-input");
            input.addEventListener("input", updateModalLivePreview);
            input.addEventListener("focus", () => { modalState.lastFocusedInput = input; });

            choicesContainer.appendChild(row);
        });
    }

    // Part 2 Items (True / False)
    if (partKey === "part2") {
        const itemsContainer = document.getElementById("modal-p2-items-container");
        itemsContainer.innerHTML = "";

        ['a', 'b', 'c', 'd'].forEach(k => {
            const item = (q.items && q.items[k]) ? q.items[k] : { text: '', correct: false };
            const isTrue = item.correct;
            const row = document.createElement("div");
            row.className = "p-2.5 rounded-xl border border-slate-200 bg-white flex items-center justify-between gap-3";
            row.innerHTML = `
                <div class="flex items-center space-x-2 flex-1">
                    <span class="font-bold text-xs text-slate-700 w-5">${k})</span>
                    <input type="text" class="modal-p2-item-input flex-1 px-3 py-1.5 text-sm font-medium border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500" data-key="${k}" value="${escapeHtml(item.text || '')}" placeholder="Nội dung lệnh hỏi ${k})...">
                </div>
                <div class="flex items-center space-x-1.5 shrink-0">
                    <button type="button" class="modal-p2-btn-toggle px-3 py-1 rounded-md text-xs font-bold transition ${isTrue ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'}" data-key="${k}" data-val="true">
                        Đúng
                    </button>
                    <button type="button" class="modal-p2-btn-toggle px-3 py-1 rounded-md text-xs font-bold transition ${!isTrue ? 'bg-rose-600 text-white' : 'bg-slate-100 text-slate-600'}" data-key="${k}" data-val="false">
                        Sai
                    </button>
                </div>
            `;

            row.querySelectorAll(".modal-p2-btn-toggle").forEach(btn => {
                btn.addEventListener("click", () => {
                    const val = (btn.dataset.val === "true");
                    if (!q.items) q.items = {};
                    if (!q.items[k]) q.items[k] = {};
                    q.items[k].correct = val;
                    openEditModal(partKey, qIndex);
                });
            });

            const input = row.querySelector(".modal-p2-item-input");
            input.addEventListener("input", updateModalLivePreview);
            input.addEventListener("focus", () => { modalState.lastFocusedInput = input; });

            itemsContainer.appendChild(row);
        });
    }

    // Part 3 Short Answer
    if (partKey === "part3") {
        const ansInput = document.getElementById("modal-p3-ans-input");
        ansInput.value = (q.answer || '').replace(/^\$|\$$/g, '');
        ansInput.addEventListener("input", updateModalLivePreview);
        ansInput.addEventListener("focus", () => { modalState.lastFocusedInput = ansInput; });
    }

    // Part 4 Guide
    if (partKey === "part4") {
        const guideText = document.getElementById("modal-p4-guide-text");
        guideText.value = (q.guide || '').replace(/<br\s*\/?>/gi, '\n');
        guideText.addEventListener("input", updateModalLivePreview);
        guideText.addEventListener("focus", () => { modalState.lastFocusedInput = guideText; });
    }

    // Update Live Preview immediately
    updateModalLivePreview();

    // Show modal
    modal.classList.remove("hidden");
    lucide.createIcons();
}

function updateModalLivePreview() {
    const partKey = modalState.activePart;
    const qIndex = modalState.qIndex;

    const previewBadge = document.getElementById("preview-q-badge");
    const previewScore = document.getElementById("preview-q-score");
    const previewContent = document.getElementById("preview-q-content");
    const previewChoices = document.getElementById("preview-choices-container");

    previewBadge.textContent = `Câu ${qIndex + 1}`;
    let scoreText = "TNKQ (0.25đ)";
    if (partKey === "part2") scoreText = "Đúng/Sai (1.0đ)";
    if (partKey === "part3") scoreText = "TL Ngắn (0.25đ)";
    if (partKey === "part4") scoreText = "Tự luận";
    previewScore.textContent = scoreText;

    const qTextVal = document.getElementById("modal-q-text").value;
    previewContent.innerHTML = formatMathPreview(qTextVal);

    previewChoices.innerHTML = "";

    if (partKey === "part1") {
        const checkedRadio = document.querySelector("input[name='modal_choice_correct']:checked");
        const correctKey = checkedRadio ? checkedRadio.value : "A";

        ['A', 'B', 'C', 'D'].forEach(k => {
            const input = document.querySelector(`.modal-choice-input[data-key='${k}']`);
            const choiceText = input ? input.value : "";
            const isCorrect = (k === correctKey);

            const row = document.createElement("div");
            row.className = `p-3 rounded-xl border transition flex items-center space-x-2.5 ${isCorrect ? 'border-2 border-emerald-500 bg-emerald-50/70 ring-2 ring-emerald-500/20' : 'border-slate-200 bg-white'}`;
            row.innerHTML = `
                <div class="w-6 h-6 rounded-full ${isCorrect ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-700'} font-bold text-xs flex items-center justify-center shrink-0">
                    ${k}
                </div>
                <div class="math-preview text-sm ${isCorrect ? 'font-bold text-emerald-950' : 'font-medium text-slate-800'} flex-1 leading-snug">
                    ${formatMathPreview(choiceText)}
                </div>
                ${isCorrect ? '<span class="text-emerald-700 font-bold text-xs bg-emerald-100 px-2 py-0.5 rounded ml-auto shrink-0">✓ Đáp án</span>' : ''}
            `;
            previewChoices.appendChild(row);
        });
    } else if (partKey === "part2") {
        ['a', 'b', 'c', 'd'].forEach(k => {
            const input = document.querySelector(`.modal-p2-item-input[data-key='${k}']`);
            const itemText = input ? input.value : "";
            const currentItem = (currentExamData.part2[qIndex]?.items && currentExamData.part2[qIndex].items[k]) ? currentExamData.part2[qIndex].items[k] : { correct: false };
            const isTrue = currentItem.correct;

            const row = document.createElement("div");
            row.className = "p-2.5 rounded-xl border border-slate-200 bg-white flex items-center justify-between gap-3";
            row.innerHTML = `
                <div class="flex items-center space-x-2.5 flex-1">
                    <span class="font-bold text-xs text-slate-700 w-5">${k})</span>
                    <div class="math-preview text-sm font-medium text-slate-800">${formatMathPreview(itemText)}</div>
                </div>
                <span class="px-2.5 py-0.5 rounded text-xs font-bold ${isTrue ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${isTrue ? 'Đúng' : 'Sai'}
                </span>
            `;
            previewChoices.appendChild(row);
        });
    } else if (partKey === "part3") {
        const ansInput = document.getElementById("modal-p3-ans-input");
        const ansVal = ansInput ? ansInput.value : "";
        previewChoices.innerHTML = `
            <div class="p-3 rounded-xl border border-amber-200 bg-amber-50/40 flex items-center space-x-2">
                <span class="text-xs font-bold text-amber-900">Đáp án điền:</span>
                <span class="math-preview text-sm font-bold text-amber-950">${formatMathPreview(ansVal)}</span>
            </div>
        `;
    } else if (partKey === "part4") {
        const guideInput = document.getElementById("modal-p4-guide-text");
        const guideVal = guideInput ? guideInput.value : "";
        previewChoices.innerHTML = `
            <div class="p-3 rounded-xl border border-purple-200 bg-purple-50/40 space-y-1">
                <span class="text-xs font-bold text-purple-900">Hướng dẫn chấm:</span>
                <div class="math-preview text-xs text-slate-800 leading-relaxed">${formatMathPreview(guideVal)}</div>
            </div>
        `;
    }

    renderMathSafe(document.getElementById("preview-q-content"));
    renderMathSafe(previewChoices);
}

function saveModalQuestion(andClose = false, andNext = false) {
    const partKey = modalState.activePart;
    const qIndex = modalState.qIndex;
    if (!currentExamData || !currentExamData[partKey]) return;

    const q = currentExamData[partKey][qIndex];
    q.question = document.getElementById("modal-q-text").value;
    q.is_edited = true;
    q.xml_strings = []; // Invalidate stale oxml so edited text is used cleanly

    if (partKey === "part1") {
        const checkedRadio = document.querySelector("input[name='modal_choice_correct']:checked");
        q.correct = checkedRadio ? checkedRadio.value : "A";
        q.has_red = true;
        if (!q.choices) q.choices = {};
        if (!q.choice_xmls) q.choice_xmls = {};

        ['A', 'B', 'C', 'D'].forEach(k => {
            const input = document.querySelector(`.modal-choice-input[data-key='${k}']`);
            q.choices[k] = input ? input.value : "";
            q.choice_xmls[k] = []; // Invalidate stale oxml
        });
    } else if (partKey === "part2") {
        if (!q.items) q.items = {};
        ['a', 'b', 'c', 'd'].forEach(k => {
            const input = document.querySelector(`.modal-p2-item-input[data-key='${k}']`);
            if (!q.items[k]) q.items[k] = { correct: false };
            q.items[k].text = input ? input.value : "";
            q.items[k].xml_strings = [];
        });
    } else if (partKey === "part3") {
        q.answer = document.getElementById("modal-p3-ans-input").value;
    } else if (partKey === "part4") {
        q.guide = document.getElementById("modal-p4-guide-text").value;
    }

    // Update main card view
    renderExamEditor(currentExamData, currentFilename);

    if (andNext) {
        navigateModal(1);
    } else if (andClose) {
        document.getElementById("question-edit-modal").classList.add("hidden");
        showToast(`Đã lưu thay đổi Câu ${qIndex + 1}!`, true);
    } else {
        showToast(`Đã lưu thay đổi Câu ${qIndex + 1}!`, true);
    }
}

function navigateModal(direction) {
    const partKey = modalState.activePart;
    const qList = currentExamData[partKey];
    if (!qList) return;

    let newIndex = modalState.qIndex + direction;
    if (newIndex >= 0 && newIndex < qList.length) {
        openEditModal(partKey, newIndex);
    } else if (newIndex >= qList.length) {
        // Move to next part
        const parts = ["part1", "part2", "part3", "part4"];
        const pIdx = parts.indexOf(partKey);
        if (pIdx < parts.length - 1 && currentExamData[parts[pIdx + 1]]?.length > 0) {
            openEditModal(parts[pIdx + 1], 0);
        } else {
            document.getElementById("question-edit-modal").classList.add("hidden");
            showToast("Đã duyệt qua toàn bộ các câu hỏi!", true);
        }
    } else if (newIndex < 0) {
        const parts = ["part1", "part2", "part3", "part4"];
        const pIdx = parts.indexOf(partKey);
        if (pIdx > 0 && currentExamData[parts[pIdx - 1]]?.length > 0) {
            const prevPart = parts[pIdx - 1];
            openEditModal(prevPart, currentExamData[prevPart].length - 1);
        }
    }
}

// KaTeX Safe Rendering Helper
function renderMathSafe(target = document.body) {
    if (window.renderMathInElement) {
        try {
            renderMathInElement(target, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                ignoredClasses: ["p3-ans-text", "modal-choice-input", "modal-p2-item-input", "exam-figure", "exam-table", "exam-image-wrap", "exam-table-wrap", "mathtype-formula", "mathtype-badge", "mathtype-placeholder"],
                throwOnError: false
            });
        } catch (e) {
            console.warn("KaTeX render error:", e);
        }
    }
}

// Sync metadata edits from UI
function collectEditsFromUI() {
    if (!currentExamData) return;

    currentExamData.metadata.school = document.getElementById("cfg-school").value || "THPT Long Cang";
    currentExamData.metadata.time = document.getElementById("cfg-time").value || "90 phút";
    currentExamData.metadata.year = document.getElementById("cfg-year").value || "2026 - 2027";

    const subSelect = document.getElementById("cfg-subject-select");
    const subOther = document.getElementById("cfg-subject-other");
    if (subSelect) {
        if (subSelect.value === "__other__") {
            currentExamData.metadata.subject = (subOther ? subOther.value.trim() : "") || "Môn khác";
        } else {
            currentExamData.metadata.subject = subSelect.value;
        }
    }
}

// Save Exam Data to Server
async function saveExamData() {
    collectEditsFromUI();
    try {
        const res = await fetch("/api/save-exam", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSessionId,
                exam_data: currentExamData
            })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Đã lưu các thay đổi đề thi thành công!", true);
        } else {
            showToast("Lỗi khi lưu: " + data.detail, false);
        }
    } catch (e) {
        showToast("Lỗi kết nối khi lưu: " + e.message, false);
    }
}

// Execute Shuffling
async function executeShuffle() {
    if (!currentExamData) {
        showToast("Vui lòng tải đề lên hoặc chọn đề mẫu trước khi trộn!", false);
        return;
    }

    collectEditsFromUI();

    const spinner = document.getElementById("shuffle-spinner");
    const resultsContainer = document.getElementById("results-container");

    spinner.classList.remove("hidden");
    resultsContainer.classList.add("hidden");

    const config = {
        num_variants: parseInt(document.getElementById("cfg-num-variants").value) || 4,
        start_code: parseInt(document.getElementById("cfg-start-code").value) || 101,
        shuffle_p1_questions: document.getElementById("cfg-shuf-p1-q").checked,
        shuffle_p1_choices: document.getElementById("cfg-shuf-p1-c").checked,
        shuffle_p2_questions: document.getElementById("cfg-shuf-p2-q").checked,
        shuffle_p2_items: document.getElementById("cfg-shuf-p2-i").checked,
        shuffle_p3_questions: document.getElementById("cfg-shuf-p3-q").checked,
        shuffle_p4_questions: document.getElementById("cfg-shuf-p4-q").checked,
        school: currentExamData.metadata.school,
        subject: currentExamData.metadata.subject,
        time: currentExamData.metadata.time,
        year: currentExamData.metadata.year
    };

    try {
        const response = await fetch("/api/shuffle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSessionId,
                exam_data: currentExamData,
                config: config
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Lỗi khi trộn đề thi");
        }

        renderResultsHub(data);
        showToast("Đã trộn đề thi thành công!", true);

        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
        showToast(err.message, false);
    } finally {
        spinner.classList.add("hidden");
        resultsContainer.classList.remove("hidden");
    }
}

// Render Results & Download Matrix
function renderResultsHub(data) {
    const container = document.getElementById("results-container");
    const variantsGrid = document.getElementById("variants-grid");
    const summary = data.summary;
    const links = data.downloads;

    // Set Master ZIP download button
    const zipBtn = document.getElementById("download-zip-btn");
    if (data.zip_base64) {
        try {
            const byteCharacters = atob(data.zip_base64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/zip' });
            const blobUrl = URL.createObjectURL(blob);
            zipBtn.href = blobUrl;
            zipBtn.download = "Bo_de_thi_tron.zip";
        } catch (e) {
            zipBtn.href = links.zip;
            zipBtn.download = "Bo_de_thi_tron.zip";
        }
    } else {
        zipBtn.href = links.zip;
        zipBtn.download = "Bo_de_thi_tron.zip";
    }

    document.getElementById("download-excel-btn").href = links.excel;
    document.getElementById("download-summary-docx-btn").href = links.summary_docx;

    // Render Variant Cards
    if (variantsGrid) {
        variantsGrid.innerHTML = "";
        if (links && Array.isArray(links.tests)) {
            links.tests.forEach((t, idx) => {
                const keyItem = (links.keys && links.keys[idx]) || { url: '#', filename: '' };
                const card = document.createElement("div");
                card.className = "bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3";
                card.innerHTML = `
                    <div class="flex items-center justify-between">
                        <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-brand-50 text-brand-700 border border-brand-200">
                            MÃ ĐỀ: ${t.code}
                        </span>
                        <span class="text-xs text-slate-400">Đề số ${idx + 1}</span>
                    </div>
                    <div class="space-y-1.5 pt-1">
                        <a href="${t.url}" download="${t.filename}" class="w-full inline-flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white transition shadow-sm">
                            <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
                            <span>Tải Đề Word (.docx)</span>
                        </a>
                        <a href="${keyItem.url}" download="${keyItem.filename}" class="w-full inline-flex items-center justify-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                            <span>Đáp Án & Lời Giải</span>
                        </a>
                    </div>
                `;
                variantsGrid.appendChild(card);
            });
        }
    }

    // Render Answer Matrix Tables
    const codes = (Array.isArray(summary?.codes) && summary.codes.length > 0)
        ? summary.codes
        : ((Array.isArray(summary?.variants) && summary.variants.length > 0)
            ? summary.variants
            : (Array.isArray(links?.tests) ? links.tests.map(t => t.code) : []));

    // 1. Part I Matrix
    const p1Thead = document.getElementById("matrix-p1-thead");
    const p1Tbody = document.getElementById("matrix-p1-tbody");
    if (p1Thead && Array.isArray(codes) && codes.length > 0) {
        p1Thead.innerHTML = `<tr><th class="p-2.5 border border-blue-900 w-16">Câu</th>${codes.map(c => `<th class="p-2.5 border border-blue-900">Mã ${c}</th>`).join('')}</tr>`;
    }
    
    if (p1Tbody) {
        p1Tbody.innerHTML = "";
        if (summary && summary.part1 && summary.part1.rows && Array.isArray(codes)) {
            summary.part1.rows.forEach((r, idx) => {
                const tr = document.createElement("tr");
                tr.className = (idx % 2 === 0) ? "bg-blue-50/30" : "bg-white";
                tr.innerHTML = `
                    <td class="p-2 border border-slate-200 font-bold text-slate-700">Câu ${r.question_num}</td>
                    ${codes.map(c => `
                        <td class="p-2 border border-slate-200 font-bold ${r[c] ? 'text-brand-700 bg-brand-50/40' : 'text-slate-400'}">
                            ${r[c] || '-'}
                        </td>
                    `).join('')}
                `;
                p1Tbody.appendChild(tr);
            });
        }
    }

    // 2. Part II Matrix
    const p2Thead = document.getElementById("matrix-p2-thead");
    const p2Tbody = document.getElementById("matrix-p2-tbody");
    if (p2Thead && Array.isArray(codes) && codes.length > 0) {
        p2Thead.innerHTML = `<tr><th class="p-2.5 border border-emerald-900 w-28 text-left pl-4">Lệnh hỏi</th>${codes.map(c => `<th class="p-2.5 border border-emerald-900">Mã ${c}</th>`).join('')}</tr>`;
    }
    
    if (p2Tbody) {
        p2Tbody.innerHTML = "";
        if (summary && summary.part2 && summary.part2.rows && Array.isArray(codes)) {
            summary.part2.rows.forEach((r, idx) => {
                const tr = document.createElement("tr");
                tr.className = (idx % 2 === 0) ? "bg-emerald-50/30" : "bg-white";
                tr.innerHTML = `
                    <td class="p-2 border border-slate-200 font-bold text-slate-700 text-left pl-4">${r.label}</td>
                    ${codes.map(c => {
                        const isTrue = (r[c] === 'Đ');
                        return `
                            <td class="p-2 border border-slate-200 font-bold ${isTrue ? 'text-emerald-700' : 'text-slate-500'}">
                                <span class="inline-flex items-center justify-center px-2 py-0.5 rounded ${isTrue ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}">
                                    ${r[c] || ''}
                                </span>
                            </td>
                        `;
                    }).join('')}
                `;
                p2Tbody.appendChild(tr);
            });
        }
    }

    // 3. Part III Matrix
    const p3Thead = document.getElementById("matrix-p3-thead");
    const p3Tbody = document.getElementById("matrix-p3-tbody");
    if (p3Thead && Array.isArray(codes) && codes.length > 0) {
        p3Thead.innerHTML = `<tr><th class="p-2.5 border border-amber-900 w-24">Câu</th>${codes.map(c => `<th class="p-2.5 border border-amber-900">Mã ${c}</th>`).join('')}</tr>`;
    }
    
    if (p3Tbody) {
        p3Tbody.innerHTML = "";
        if (summary && summary.part3 && summary.part3.rows && Array.isArray(codes)) {
            summary.part3.rows.forEach((r, idx) => {
                const tr = document.createElement("tr");
                tr.className = (idx % 2 === 0) ? "bg-amber-50/30" : "bg-white";
                tr.innerHTML = `
                    <td class="p-2 border border-slate-200 font-bold text-slate-700">Câu ${r.question_num}</td>
                    ${codes.map(c => `
                        <td class="p-2 border border-slate-200 text-amber-900 font-bold">
                            ${r[c] || ''}
                        </td>
                    `).join('')}
                `;
                p3Tbody.appendChild(tr);
            });
        }
    }

    // 4. Part IV Matrix (Tự luận)
    const p4Container = document.getElementById("matrix-p4-container");
    const p4Thead = document.getElementById("matrix-p4-thead");
    const p4Tbody = document.getElementById("matrix-p4-tbody");
    if (summary && summary.part4 && summary.part4.rows && summary.part4.rows.length > 0) {
        if (p4Container) p4Container.classList.remove("hidden");
        if (p4Thead && Array.isArray(codes) && codes.length > 0) {
            p4Thead.innerHTML = `<tr><th class="p-2.5 border border-purple-900 w-24 text-center">Câu</th>${codes.map(c => `<th class="p-2.5 border border-purple-900">Mã ${c}</th>`).join('')}</tr>`;
        }
        if (p4Tbody && Array.isArray(codes)) {
            p4Tbody.innerHTML = "";
            summary.part4.rows.forEach((r, idx) => {
                const tr = document.createElement("tr");
                tr.className = (idx % 2 === 0) ? "bg-purple-50/30" : "bg-white";
                tr.innerHTML = `
                    <td class="p-2 border border-slate-200 font-bold text-slate-700 text-center">Câu ${r.question_num}</td>
                    ${codes.map(c => {
                        const val = r[c] || {};
                        const guideText = (typeof val === 'object') ? (val.guide || val.question || '') : String(val || '');
                        return `
                            <td class="p-2 border border-slate-200 text-slate-800 text-xs">
                                ${formatMathPreview(guideText)}
                            </td>
                        `;
                    }).join('')}
                `;
                p4Tbody.appendChild(tr);
            });
        }
    } else {
        if (p4Container) p4Container.classList.add("hidden");
    }

    lucide.createIcons();
    renderMathSafe(container);
}

// Escape HTML utility
function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Clean and format math formulas for crisp KaTeX rendering & safely escape HTML tags
function formatMathPreview(html) {
    if (!html) return "";
    let s = String(html);

    // Mask system HTML elements (tables, images, MathType, sub, sup, br)
    // All other tags like <head>, <body>, <b>, <td>, <p style='...'> are USER CODE and will be safely escaped!
    const placeholders = [];
    const systemPattern = /(<div class="exam-[^"]*"[\s\S]*?<\/div>|<table class="exam-table"[\s\S]*?<\/table>|<img\s+[^>]*class=["']?(?:mathtype-formula|exam-figure)["']?[^>]*>|<span class="mathtype-[^"]*"[\s\S]*?<\/span>|<\/?sub>|<\/?sup>|<br\s*\/?>)/gi;

    s = s.replace(systemPattern, (m) => {
        placeholders.push(m);
        return `___SYS_TAG_${placeholders.length - 1}___`;
    });

    // Escape all user non-system HTML brackets so <head>, <b>, <td>, etc. do NOT break the DOM!
    s = s.replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // 0. Unescape double backslashes before LaTeX keywords and braces
    s = s.replace(/\\\\([a-zA-Z{}])/g, "\\$1");

    // 1. Clean nested \left\{ and \right. or \right) around \begin{cases}, \begin{aligned}, \begin{matrix}
    s = s.replace(/\\left\\{\s*\\begin\{(?:cases|aligned|matrix)\}([\s\S]*?)\\end\{(?:cases|aligned|matrix)\}\s*(?:\\right[\.\)]?)?/g, "\\begin{cases}$1\\end{cases}");
    s = s.replace(/(?:\\left\\{|\{)\s*\\begin\{(?:matrix|aligned)\}([\s\S]*?)\\end\{(?:matrix|aligned)\}\s*(?:\\right[\.\)]?|\})?/g, "\\begin{cases}$1\\end{cases}");

    // 2. Convert standalone \begin{aligned} to \begin{cases}
    s = s.replace(/\\begin\{aligned\}([\s\S]*?)\\end\{aligned\}/g, "\\begin{cases}$1\\end{cases}");

    // 3. Clean and collapse any malformed wraps like ${\$\begin{cases} ... \end{cases}$$, etc.
    s = s.replace(
        /(?:\\left\\{|\{)?\s*\\?\$*\s*(?:\\left\\{|\{)?\s*\\?\$*\s*\\begin\{cases\}([\s\S]*?)\\end\{cases\}\s*(?:\\right[\.\)]?|\})?\s*\\?\$*\s*(?:\\right[\.\)]?|\})?\s*\\?\$*/g,
        "$\\begin{cases}$1\\end{cases}$"
    );

    // 4. Ensure space around $\begin{cases} if abutting regular letters
    s = s.replace(/([^\s\$])(\$\\begin\{cases\})/g, "$1 $2");
    s = s.replace(/(\\end\{cases\}\$)([^\s\$\.\,\;\:\?\!])/g, "$1 $2");

    // 5. Convert unicode vector arrows (e.g. u\u20d7, a\u20d7, u⃗, a⃗, AB⃗) into KaTeX $\vec{...}$
    s = s.replace(/([A-Za-z]{1,3})[\u20D7\u2192\u20D6⃗]/g, "$\\vec{$1}$");
    s = s.replace(/(?<!\$)\\vec\s*\{([A-Za-z0-9]{1,4})\}(?!\$)/g, "$\\vec{$1}$");

    // 6. Ensure common standalone LaTeX math commands are wrapped in $ if naked:
    s = s.replace(/(?<!\$)\\frac\{([^{}]+)\}\{([^{}]+)\}(?!\$)/g, "$\\frac{$1}{$2}$");
    s = s.replace(/(?<!\$)\\sqrt\{([^{}]+)\}(?!\$)/g, "$\\sqrt{$1}$");
    s = s.replace(/(?<!\$)\\sqrt\[([^\[\]]+)\]\{([^{}]+)\}(?!\$)/g, "$\\sqrt[$1]{$2}$");

    // 7. If text contains naked math commands (e.g. "m \neq 6", "x \ge 2", "\int_0^1 x dx") and no $, wrap it in $
    if (!s.includes("$") && /\\[a-zA-Z]+/.test(s)) {
        s = "$" + s.trim() + "$";
    }

    // 8. Clean up soft hyphens and unicode artifacts from PDF
    s = s.replace(/\u00ad/g, "-");
    s = s.replace(/\u2212/g, "-");
    s = s.replace(/\u037e/g, ";");

    // Restore protected system tags
    placeholders.forEach((ph, i) => {
        s = s.replace(`___SYS_TAG_${i}___`, ph);
    });

    return s;
}
