// Frontend Logic for Exam Shuffler

let currentSessionId = null;
let currentExamData = null;
let currentFilename = "";

document.addEventListener("DOMContentLoaded", () => {
    initEvents();
});

function showToast(message, isSuccess = true) {
    const toast = document.getElementById("toast");
    const msgEl = document.getElementById("toast-msg");
    const iconEl = document.getElementById("toast-icon");
    
    msgEl.textContent = message;
    if (isSuccess) {
        iconEl.setAttribute("data-lucide", "check-circle");
        iconEl.className = "w-5 h-5 text-emerald-400";
    } else {
        iconEl.setAttribute("data-lucide", "alert-triangle");
        iconEl.className = "w-5 h-5 text-rose-400";
    }
    lucide.createIcons();

    toast.classList.remove("translate-y-20", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");

    setTimeout(() => {
        toast.classList.remove("translate-y-0", "opacity-100");
        toast.classList.add("translate-y-20", "opacity-0");
    }, 3500);
}

function initEvents() {
    // Tab switching
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

    // Subject dropdown change event
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

    // 1-Click Sample Exam Loader
    const btnLoadSample = document.getElementById("btn-load-sample");
    if (btnLoadSample) {
        btnLoadSample.addEventListener("click", () => {
            loadSampleExam();
        });
    }
    const btnLoadSampleHero = document.getElementById("btn-load-sample-hero");
    if (btnLoadSampleHero) {
        btnLoadSampleHero.addEventListener("click", () => {
            loadSampleExam();
        });
    }

    // Save Exam
    document.getElementById("btn-save-exam").addEventListener("click", () => {
        saveExamData();
    });

    // Execute Shuffle
    document.getElementById("btn-execute-shuffle").addEventListener("click", () => {
        executeShuffle();
    });
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
    if (schoolInput) {
        schoolInput.value = data.metadata.school || "THPT Long Cang";
    }
    const yearInput = document.getElementById("cfg-year");
    if (yearInput) {
        yearInput.value = data.metadata.year || "2026 - 2027";
    }
    if (data.metadata.time) {
        document.getElementById("cfg-time").value = data.metadata.time;
    }

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

    document.getElementById("stat-p1-count").textContent = p1Count;
    document.getElementById("stat-p2-count").textContent = p2Count;
    document.getElementById("stat-p3-count").textContent = p3Count;
    document.getElementById("stat-p4-count").textContent = p4Count;

    document.getElementById("p1-counter-tag").textContent = `${p1Count} câu`;
    document.getElementById("p2-counter-tag").textContent = `${p2Count} câu`;
    document.getElementById("p3-counter-tag").textContent = `${p3Count} câu`;
    document.getElementById("p4-counter-tag").textContent = `${p4Count} câu`;

    // 1. Render Part I Questions
    const p1Container = document.getElementById("p1-questions-list");
    p1Container.innerHTML = "";
    if (data.part1) {
        data.part1.forEach((q, idx) => {
            const card = document.createElement("div");
            card.className = "pt-4 first:pt-0 space-y-3";
            
            const redBadge = q.has_red ? 
                `<span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                    <span class="w-1.5 h-1.5 rounded-full bg-rose-600 inline-block"></span>
                    <span>Đã nhận diện đáp án: ${q.correct}</span>
                 </span>` : 
                `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                    Đáp án mặc định: ${q.correct}
                 </span>`;

            card.innerHTML = `
                <div class="flex items-start justify-between gap-2">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 rounded-md bg-blue-600 text-white font-bold text-xs shadow-sm">Câu ${idx + 1}</span>
                        ${redBadge}
                    </div>
                    <span class="text-xs text-slate-400 font-medium">Gốc: Câu ${q.original_num || (idx+1)}</span>
                </div>
                <div class="space-y-1.5">
                    <div class="math-preview p-3.5 rounded-xl bg-blue-50/40 border border-blue-200 text-sm text-slate-900 leading-relaxed font-sans shadow-sm" id="p1-prev-q-${idx}">${formatMathPreview(q.question)}</div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                    ${['A', 'B', 'C', 'D'].map(k => {
                        const isCorrect = (q.correct === k);
                        return `
                            <div class="choice-math-card cursor-pointer p-3 rounded-xl border transition-all duration-150 ${isCorrect ? 'border-brand-500 bg-brand-50/70 ring-2 ring-brand-500 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'} flex items-start space-x-2.5" data-qidx="${idx}" data-key="${k}">
                                <input type="radio" name="p1_correct_${idx}" value="${k}" ${isCorrect ? 'checked' : ''} class="p1-choice-radio mt-0.5 text-brand-600 focus:ring-brand-500 pointer-events-none" data-qidx="${idx}">
                                <div class="flex-1">
                                    <span class="font-bold text-xs ${isCorrect ? 'text-brand-700' : 'text-slate-700'} mr-1.5">${k}.</span>
                                    <span class="math-preview text-sm ${isCorrect ? 'font-bold text-brand-900' : 'font-semibold text-slate-800'}" id="p1-prev-c-${idx}-${k}">${formatMathPreview(q.choices[k] || '')}</span>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
            p1Container.appendChild(card);
        });
    }

    // 2. Render Part II Questions
    const p2Container = document.getElementById("p2-questions-list");
    p2Container.innerHTML = "";
    if (data.part2) {
        data.part2.forEach((q, idx) => {
            const card = document.createElement("div");
            card.className = "pt-4 first:pt-0 space-y-3";
            card.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-1 rounded-md bg-emerald-600 text-white font-bold text-xs shadow-sm">Câu ${idx + 1}</span>
                    <span class="text-xs text-slate-400 font-medium">Gốc: Câu ${q.original_num || (idx+1)}</span>
                </div>
                <div class="space-y-1.5">
                    <div class="math-preview p-3.5 rounded-xl bg-emerald-50/40 border border-emerald-200 text-sm text-slate-900 leading-relaxed font-sans shadow-sm" id="p2-prev-q-${idx}">${formatMathPreview(q.question)}</div>
                </div>
                <div class="space-y-2 pt-1">
                    ${['a', 'b', 'c', 'd'].map(k => {
                        const item = q.items[k] || { text: '', correct: false };
                        const isTrue = item.correct;
                        return `
                            <div class="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between gap-3 shadow-xs">
                                <div class="flex items-center space-x-2.5 flex-1">
                                    <span class="font-bold text-xs text-slate-700 w-5">${k})</span>
                                    <div class="math-preview text-sm font-medium text-slate-800" id="p2-prev-item-${idx}-${k}">${formatMathPreview(item.text || '')}</div>
                                </div>
                                <div class="flex items-center space-x-1.5 shrink-0">
                                    <button type="button" class="p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-xs ${isTrue ? 'bg-emerald-600 text-white shadow-emerald-500/20' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}" data-qidx="${idx}" data-key="${k}" data-val="true">
                                        Đúng
                                    </button>
                                    <button type="button" class="p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-xs ${!isTrue ? 'bg-rose-600 text-white shadow-rose-500/20' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}" data-qidx="${idx}" data-key="${k}" data-val="false">
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

    // 3. Render Part III Questions
    const p3Container = document.getElementById("p3-questions-list");
    p3Container.innerHTML = "";
    if (data.part3) {
        data.part3.forEach((q, idx) => {
            const card = document.createElement("div");
            card.className = "pt-4 first:pt-0 space-y-3";
            card.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-1 rounded-md bg-amber-600 text-white font-bold text-xs shadow-sm">Câu ${idx + 1}</span>
                    <span class="text-xs text-slate-400 font-medium">Gốc: Câu ${q.original_num || (idx+1)}</span>
                </div>
                <div class="space-y-1.5">
                    <div class="math-preview p-3.5 rounded-xl bg-amber-50/40 border border-amber-200 text-sm text-slate-900 leading-relaxed font-sans shadow-sm" id="p3-prev-q-${idx}">${formatMathPreview(q.question)}</div>
                </div>
                <div class="flex items-center space-x-3 pt-1">
                    <label class="text-xs font-bold text-slate-700">Đáp án:</label>
                    <input type="text" value="${escapeHtml(q.answer || '')}" class="p3-ans-text w-36 px-3 py-1.5 text-xs font-bold border border-amber-300 rounded-lg bg-amber-50/50 text-amber-900 outline-none focus:ring-2 focus:ring-amber-500" data-idx="${idx}" placeholder="Nhập đáp số...">
                </div>
            `;
            p3Container.appendChild(card);
        });
    }

    // 4. Render Part IV Questions
    const p4Container = document.getElementById("p4-questions-list");
    p4Container.innerHTML = "";
    if (data.part4) {
        data.part4.forEach((q, idx) => {
            const card = document.createElement("div");
            card.className = "pt-4 first:pt-0 space-y-3";
            card.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-1 rounded-md bg-purple-600 text-white font-bold text-xs shadow-sm">Câu ${idx + 1}</span>
                    <span class="text-xs text-slate-400 font-medium">Gốc: Câu ${q.original_num || (idx+1)}</span>
                </div>
                <div class="space-y-1.5">
                    <div class="math-preview p-3.5 rounded-xl bg-purple-50/40 border border-purple-200 text-sm text-slate-900 leading-relaxed font-sans shadow-sm" id="p4-prev-q-${idx}">${formatMathPreview(q.question)}</div>
                </div>
                ${q.guide ? `
                <div class="space-y-1 pt-1">
                    <label class="text-xs text-purple-700 font-bold">Hướng dẫn chấm & Thang điểm:</label>
                    <div class="math-preview p-3.5 rounded-xl bg-purple-50/40 border border-purple-200 text-xs text-slate-800 leading-relaxed font-sans shadow-sm" id="p4-prev-guide-${idx}">${formatMathPreview(q.guide)}</div>
                </div>
                ` : ''}
            `;
            p4Container.appendChild(card);
        });
    }

    // Attach listeners for interactive edits
    attachEditorListeners();

    // Re-render Lucide icons
    lucide.createIcons();

    // Render KaTeX for all math previews
    renderMathSafe(document.body);
}

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
                ignoredClasses: ["p3-ans-text"],
                throwOnError: false
            });
        } catch (e) {
            console.warn("KaTeX render error:", e);
        }
    }
}

function attachEditorListeners() {
    // Clickable choice cards for Part I answers
    document.querySelectorAll(".choice-math-card").forEach(card => {
        card.addEventListener("click", (e) => {
            const qIdx = parseInt(card.dataset.qidx);
            const key = card.dataset.key;
            currentExamData.part1[qIdx].correct = key;
            currentExamData.part1[qIdx].has_red = true;

            const parentGrid = card.closest(".grid");
            if (parentGrid) {
                parentGrid.querySelectorAll(".choice-math-card").forEach(c => {
                    const isSelected = (c.dataset.key === key);
                    c.className = `choice-math-card cursor-pointer p-3 rounded-xl border transition-all duration-150 ${isSelected ? 'border-brand-500 bg-brand-50/70 ring-2 ring-brand-500 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'} flex items-start space-x-2.5`;
                    const r = c.querySelector("input[type='radio']");
                    if (r) r.checked = isSelected;
                    const badge = c.querySelector("span.font-bold");
                    if (badge) badge.className = `font-bold text-xs ${isSelected ? 'text-brand-700' : 'text-slate-700'} mr-1.5`;
                });
            }
        });
    });

    // Part II Toggle buttons (True/False)
    document.querySelectorAll(".p2-toggle-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const qIdx = parseInt(e.target.dataset.qidx);
            const key = e.target.dataset.key;
            const isTrue = (e.target.dataset.val === "true");

            currentExamData.part2[qIdx].items[key].correct = isTrue;

            const parentDiv = e.target.closest(".flex.items-center.space-x-1\\.5");
            if (parentDiv) {
                const btnTrue = parentDiv.querySelector('[data-val="true"]');
                const btnFalse = parentDiv.querySelector('[data-val="false"]');

                if (isTrue) {
                    btnTrue.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-xs bg-emerald-600 text-white shadow-emerald-500/20";
                    btnFalse.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-xs bg-slate-100 text-slate-600 hover:bg-slate-200";
                } else {
                    btnTrue.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-xs bg-slate-100 text-slate-600 hover:bg-slate-200";
                    btnFalse.className = "p2-toggle-btn px-3 py-1 rounded-md text-xs font-bold transition shadow-xs bg-rose-600 text-white shadow-rose-500/20";
                }
            }
        });
    });

    // Part III Answer input
    document.querySelectorAll(".p3-ans-text").forEach(input => {
        input.addEventListener("input", (e) => {
            const idx = parseInt(e.target.dataset.idx);
            currentExamData.part3[idx].answer = e.target.value;
        });
    });

    // Live update preview for Part 4 question and guide
    document.querySelectorAll(".p4-q-text").forEach(textarea => {
        textarea.addEventListener("input", (e) => {
            const idx = parseInt(e.target.dataset.idx);
            currentExamData.part4[idx].question = e.target.value;
            const prev = document.getElementById(`p4-prev-q-${idx}`);
            if (prev) {
                prev.textContent = e.target.value;
                renderMathSafe(prev);
            }
        });
    });
    document.querySelectorAll(".p4-guide-text").forEach(textarea => {
        textarea.addEventListener("input", (e) => {
            const idx = parseInt(e.target.dataset.idx);
            currentExamData.part4[idx].guide = e.target.value;
            const prev = document.getElementById(`p4-prev-guide-${idx}`);
            if (prev) {
                prev.textContent = e.target.value;
                renderMathSafe(prev);
            }
        });
    });
}

// Sync all text edits from inputs to currentExamData
function collectEditsFromUI() {
    if (!currentExamData) return;

    // Part 1
    document.querySelectorAll(".p1-q-text").forEach(el => {
        const idx = parseInt(el.dataset.idx);
        currentExamData.part1[idx].question = el.value;
    });
    document.querySelectorAll(".p1-choice-text").forEach(el => {
        const idx = parseInt(el.dataset.qidx);
        const k = el.dataset.key;
        currentExamData.part1[idx].choices[k] = el.value;
    });

    // Part 2
    document.querySelectorAll(".p2-q-text").forEach(el => {
        const idx = parseInt(el.dataset.idx);
        currentExamData.part2[idx].question = el.value;
    });
    document.querySelectorAll(".p2-item-text").forEach(el => {
        const idx = parseInt(el.dataset.qidx);
        const k = el.dataset.key;
        currentExamData.part2[idx].items[k].text = el.value;
    });

    // Part 3
    document.querySelectorAll(".p3-q-text").forEach(el => {
        const idx = parseInt(el.dataset.idx);
        currentExamData.part3[idx].question = el.value;
    });
    document.querySelectorAll(".p3-ans-text").forEach(el => {
        const idx = parseInt(el.dataset.idx);
        currentExamData.part3[idx].answer = el.value;
    });

    // Part 4
    document.querySelectorAll(".p4-q-text").forEach(el => {
        const idx = parseInt(el.dataset.idx);
        currentExamData.part4[idx].question = el.value;
    });
    document.querySelectorAll(".p4-guide-text").forEach(el => {
        const idx = parseInt(el.dataset.idx);
        currentExamData.part4[idx].guide = el.value;
    });

    // Metadata config
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
        shuffle_p4_questions: document.getElementById("cfg-shuf-p4-q").checked
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
            throw new Error(data.detail || "Lỗi trong quá trình trộn đề");
        }

        renderResults(data);
        showToast(`Đã trộn thành công ${data.variants_count} mã đề thi!`, true);
        
        // Scroll smoothly to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        showToast("Lỗi khi trộn đề: " + err.message, false);
    } finally {
        spinner.classList.add("hidden");
    }
}

// Render Results & Download Center
function renderResults(data) {
    const container = document.getElementById("results-container");
    container.classList.remove("hidden");

    const downloads = data.downloads;
    const summary = data.summary;
    const codes = summary.codes || [];

    // Download Links
    document.getElementById("btn-download-zip").href = downloads.zip;
    document.getElementById("btn-download-excel").href = downloads.excel;
    document.getElementById("btn-download-summary-docx").href = downloads.summary_docx;

    // Variants Download Grid
    const variantsGrid = document.getElementById("variants-download-grid");
    variantsGrid.innerHTML = "";

    downloads.tests.forEach((testItem, idx) => {
        const keyItem = downloads.keys[idx];
        const card = document.createElement("div");
        card.className = "bg-slate-800/90 border border-slate-700 rounded-xl p-3.5 space-y-2.5";
        card.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 rounded bg-brand-500/20 text-brand-300 font-bold text-xs">Mã đề: ${testItem.code}</span>
                <span class="text-[10px] text-slate-400">DOCX</span>
            </div>
            <div class="space-y-1.5">
                <a href="${testItem.url}" class="w-full flex items-center justify-center space-x-1.5 py-1.5 rounded-lg text-xs font-bold bg-slate-700 hover:bg-slate-600 text-white transition">
                    <i data-lucide="file-text" class="w-3.5 h-3.5 text-blue-400"></i>
                    <span>Tải Đề Thi</span>
                </a>
                <a href="${keyItem.url}" class="w-full flex items-center justify-center space-x-1.5 py-1.5 rounded-lg text-xs font-bold bg-rose-950/60 hover:bg-rose-900/80 text-rose-200 border border-rose-800/40 transition">
                    <i data-lucide="check" class="w-3.5 h-3.5 text-rose-400"></i>
                    <span>Đáp Án Chi Tiết</span>
                </a>
            </div>
        `;
        variantsGrid.appendChild(card);
    });

    // --- RENDER LIVE MATRIX TABLES ---

    // 1. Part I Matrix
    const p1Thead = document.getElementById("matrix-p1-thead");
    const p1Tbody = document.getElementById("matrix-p1-tbody");
    p1Thead.innerHTML = `<tr><th class="p-2.5 border border-blue-900 w-16">Câu</th>${codes.map(c => `<th class="p-2.5 border border-blue-900">Mã ${c}</th>`).join('')}</tr>`;
    
    p1Tbody.innerHTML = "";
    if (summary.part1 && summary.part1.rows) {
        summary.part1.rows.forEach((r, idx) => {
            const tr = document.createElement("tr");
            tr.className = (idx % 2 === 0) ? "bg-slate-50/60" : "bg-white";
            tr.innerHTML = `
                <td class="p-2 border border-slate-200 font-bold text-slate-700">Câu ${r.question_num}</td>
                ${codes.map(c => `
                    <td class="p-2 border border-slate-200">
                        <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-50 text-blue-700 font-bold text-xs">
                            ${r[c] || ''}
                        </span>
                    </td>
                `).join('')}
            `;
            p1Tbody.appendChild(tr);
        });
    }

    // 2. Part II Matrix
    const p2Thead = document.getElementById("matrix-p2-thead");
    const p2Tbody = document.getElementById("matrix-p2-tbody");
    p2Thead.innerHTML = `<tr><th class="p-2.5 border border-emerald-900 w-28 text-left pl-4">Lệnh hỏi</th>${codes.map(c => `<th class="p-2.5 border border-emerald-900">Mã ${c}</th>`).join('')}</tr>`;
    
    p2Tbody.innerHTML = "";
    if (summary.part2 && summary.part2.rows) {
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

    // 3. Part III Matrix
    const p3Thead = document.getElementById("matrix-p3-thead");
    const p3Tbody = document.getElementById("matrix-p3-tbody");
    p3Thead.innerHTML = `<tr><th class="p-2.5 border border-amber-900 w-24">Câu</th>${codes.map(c => `<th class="p-2.5 border border-amber-900">Mã ${c}</th>`).join('')}</tr>`;
    
    p3Tbody.innerHTML = "";
    if (summary.part3 && summary.part3.rows) {
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

// Clean and format math formulas for crisp KaTeX rendering across Grade 6-12
function formatMathPreview(html) {
    if (!html) return "";
    let s = String(html);

    // 1. Clean nested \left\{ and \right. around \begin{cases} or \begin{aligned}
    s = s.replace(/\\left\\{\s*\\begin\{(cases|aligned)\}/g, "\\begin{$1}");
    s = s.replace(/\\end\{(cases|aligned)\}\s*\\right\.?/g, "\\end{$1}");

    // 2. Convert \begin{aligned} to \begin{cases}
    s = s.replace(/\\begin\{aligned\}([\s\S]*?)\\end\{aligned\}/g, "\\begin{cases}$1\\end{cases}");

    // 3. Clean and collapse any malformed wraps like ${\$\begin{cases} ... \end{cases}$$, ${\begin{cases} ... \end{cases}$, etc.
    s = s.replace(
        /(?:\\left\\{|\{)?\s*\\?\$*\s*(?:\\left\\{|\{)?\s*\\?\$*\s*\\begin\{cases\}([\s\S]*?)\\end\{cases\}\s*(?:\\right\.?|\})?\s*\\?\$*\s*(?:\\right\.?|\})?\s*\\?\$*/g,
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

    // 7. Clean up soft hyphens and unicode artifacts from PDF
    s = s.replace(/\u00ad/g, "-");
    s = s.replace(/\u2212/g, "-");
    s = s.replace(/\u037e/g, ";");

    return s;
}
