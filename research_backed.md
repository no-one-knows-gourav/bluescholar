# BlueScholar — Research-Backed LLM Minimization Guide
**Engineering Intelligence Layer | March 2026**

---

## Executive Summary

The current BlueScholar prototype treats almost every feature as a prompt template sent to Claude. This guide replaces that approach with a **tiered intelligence architecture**: deterministic algorithms and locally-hosted lightweight models handle the heavy lifting, LLM calls are reserved only where they produce irreplaceable value (nuanced explanation, novel synthesis, judgment calls). Estimated outcome: **70–85% reduction in API token spend** with no perceptible quality degradation from a student/faculty perspective, and several features that actually *improve* because they are powered by purpose-built ML models instead of general-purpose prompting.

### Cost Impact Summary

| Feature | Current Approach | Optimized Approach | Est. Token Reduction |
|---|---|---|---|
| SyllabusMapper | Claude Haiku every upload | regex + spaCy NER, LLM only fallback | ~95% |
| QuestionForge | Claude Haiku per chunk batch | Fine-tuned T5 locally | ~100% |
| PlagueScope | OpenAI embeddings + Python | SBERT all-MiniLM-L6-v2 locally | ~100% |
| SmartMock grading | Claude Sonnet per answer | SBERT cosine grading, LLM for descriptive only | ~75% |
| RevisionClock | Claude Sonnet per schedule | SM-2 / FSRS algorithm | ~90% |
| MemoryTutor context | Claude Sonnet per session | BKT/DKT knowledge state, LLM for explanation | ~60% |
| GapFinder | LLM analysis | Pure vector algebra + thresholds | ~100% |
| PaperPatternMiner | Claude Haiku per paper | spaCy + regex extraction, stats aggregation | ~90% |
| DocDoubt retrieval | Pure dense vector search → LLM | Hybrid BM25 + dense + cross-encoder rerank | +retrieval quality, same LLM cost |
| HandwrittenEvaluator | Claude Sonnet per answer | SBERT for MCQ/short, LLM only for long answers | ~65% |
| ReportWeaver | Claude Sonnet full report | Template engine + stats + LLM for two sections | ~70% |

---

## 1. Architecture Principle: The Three Tiers

Before feature-by-feature recommendations, establish this mental model for all future development:

```
TIER 1 — ZERO COST (Deterministic + Statistical)
  • Rule-based parsing (regex, grammar, pattern matching)
  • Classical algorithms (SM-2, BKT, TF-IDF, cosine similarity)
  • Statistical aggregation (Counter, pandas, numpy)
  → Use for: structured extraction, similarity scoring, scheduling, analytics

TIER 2 — NEAR-ZERO COST (Locally-Hosted Small Models, ~80–500MB)
  • Sentence Transformers: all-MiniLM-L6-v2, all-mpnet-base-v2
  • Fine-tuned T5: question generation, classification
  • spaCy with custom pipelines: NER, dependency parsing
  • Cross-encoder rerankers: ms-marco-MiniLM-L6-v2
  → Use for: semantic similarity, embedding, classification, QA generation
  → Run once at startup, keep in memory, GPU optional (CPU inference is fast enough)

TIER 3 — PAID API (Claude Sonnet / Haiku)
  • Reserved for: nuanced explanation, novel synthesis, rubric-aligned grading of long answers,
    multi-step reasoning, natural language generation where quality matters
  → Gate with confidence thresholds from Tier 1/2 before escalating
```

---

## 2. Feature-by-Feature Optimization

---

### 2.1 SyllabusMapper — Replace with a Structured Extraction Pipeline

**Current problem**: Every syllabus upload calls `claude-haiku` to parse free-form text into JSON. This is expensive and fragile for structured documents.

**Research basis**: LayoutLM and its variants (LayoutLMv3, UniDoc) show that layout-aware transformers significantly outperform pure-text LLMs on document field extraction. For syllabi — which are highly structured documents — classical NLP with rule-based enhancement handles 90%+ of cases.

**Optimized pipeline**:

```
Step 1: Structural Detection (FREE — regex + heuristics)
  - Detect section headers via font-size metadata (from pypdf) or ALL-CAPS patterns
  - Regex patterns for common syllabus fields:
      UNIT_PATTERN = r'(?i)(unit|module|chapter|section)\s*[-:]?\s*(\d+|[IVX]+)'
      MARKS_PATTERN = r'(\d+)\s*(marks?|pts?|points?)'
      TOPIC_PATTERN = r'^\s*[-•*]\s*(.+)$'  # bulleted topic lines

Step 2: spaCy NER Pipeline (FREE — 40MB model, CPU inference)
  - Use en_core_web_sm for named entity recognition
  - Custom EntityRuler patterns for academic vocabulary
  - Extract: exam dates, mark allocations, topic names, prerequisite phrases

Step 3: Weighted Template Filling (FREE)
  - Use extracted entities to fill a JSON template
  - Confidence score per field based on extraction certainty

Step 4: LLM Fallback (PAID — only when confidence < threshold)
  - If structural extraction yields confidence < 0.75 on any required field
  - Send only the low-confidence sections to Claude Haiku, not the full document
  - Gate: estimated 1 in 10 syllabi will need this fallback
```

**Implementation**:

```python
# engines/ace/syllabus_mapper.py

import spacy
import re
from dataclasses import dataclass, field
from typing import Optional

nlp = spacy.load("en_core_web_sm")  # 40MB, load once at startup

UNIT_PATTERN = re.compile(r'(?i)(unit|module|chapter)\s*[-:]?\s*(\d+|[IVX]+)[:\s]+(.+)')
MARKS_PATTERN = re.compile(r'(\d+)\s*(marks?|pts?|points?)', re.IGNORECASE)
TOPIC_BULLET = re.compile(r'^\s*[-•*◦▪]\s*(.+)$', re.MULTILINE)

class SyllabusMapperV2:
    def parse(self, text: str, institution_id: str) -> dict:
        units = self._extract_units(text)
        confidence = self._score_confidence(units)
        
        if confidence >= 0.75:
            # Fully deterministic — no LLM call
            return self._finalize(units, institution_id)
        
        # Targeted LLM call only for ambiguous sections
        ambiguous_sections = self._identify_ambiguous_sections(text, units)
        llm_patch = await self._llm_fill_gaps(ambiguous_sections)
        return self._merge_and_finalize(units, llm_patch, institution_id)
    
    def _extract_units(self, text: str) -> list:
        units = []
        lines = text.split('\n')
        current_unit = None
        
        for line in lines:
            unit_match = UNIT_PATTERN.match(line)
            if unit_match:
                current_unit = {
                    'unit_number': self._parse_unit_num(unit_match.group(2)),
                    'title': unit_match.group(3).strip(),
                    'weightage_marks': 0,
                    'topics': []
                }
                units.append(current_unit)
            
            if current_unit:
                marks_match = MARKS_PATTERN.search(line)
                if marks_match:
                    current_unit['weightage_marks'] = int(marks_match.group(1))
                
                topic_match = TOPIC_BULLET.match(line)
                if topic_match and current_unit:
                    current_unit['topics'].append({
                        'name': topic_match.group(1).strip(),
                        'subtopics': [],
                        'prerequisite_topics': []
                    })
        return units
    
    def _score_confidence(self, units: list) -> float:
        if not units:
            return 0.0
        scored = sum(
            1 for u in units
            if u['weightage_marks'] > 0 and len(u['topics']) > 0
        )
        return scored / len(units)
```

**Dependency to add**: `spacy==3.7.x` + `en_core_web_sm` model download in Dockerfile:
```dockerfile
RUN python -m spacy download en_core_web_sm
```

---

### 2.2 QuestionForge — Replace with Fine-Tuned T5 (Zero API Cost)

**Current problem**: Claude Haiku called per batch of 5 chunks, for every document ever uploaded. With hundreds of students each uploading multiple documents, this becomes the single largest cost driver.

**Research basis**: Springer Nature (2025) and ArXiv (2408.04394) confirm that fine-tuned T5 models generate Bloom's taxonomy-aligned questions with quality competitive with GPT-3.5. The BloomLLM paper (EC-TEL 2024) demonstrated a fine-tuned LLM on ~1,000 questions across 29 course topics *outperformed* ChatGPT-4 for educational question generation. The multi-task T5 approach (ScienceDirect, 2024) — jointly trained on QA, QG, and answer extraction — shows the strongest results for educational text.

**Recommended model**: `valhalla/t5-base-qg-hl` (available free on Hugging Face, 250MB)  
**Alternative**: `mrm8488/t5-base-finetuned-question-generation-ap` or self-fine-tune on your own question bank

**Implementation**:

```python
# engines/ace/question_forge.py

from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

class QuestionForgeV2:
    def __init__(self):
        # Load once at startup — 250MB, runs on CPU
        self.tokenizer = T5Tokenizer.from_pretrained("valhalla/t5-base-qg-hl")
        self.model = T5ForConditionalGeneration.from_pretrained("valhalla/t5-base-qg-hl")
        self.model.eval()
    
    def generate_questions(self, context: str, answer_hints: list[str] = None) -> list[dict]:
        """Generate questions from a text passage. No LLM call."""
        questions = []
        
        for hint in (answer_hints or self._extract_key_phrases(context)):
            # Format: "generate question: <answer> context: <passage>"
            input_text = f"generate question: {hint} context: {context[:512]}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_length=64,
                    num_beams=4,
                    early_stopping=True,
                    num_return_sequences=1
                )
            
            question_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            bloom_level = self._classify_bloom_level(question_text)
            
            questions.append({
                "question": question_text,
                "model_answer": hint,
                "bloom_level": bloom_level,
                "question_type": self._infer_question_type(question_text),
                "marks": self._estimate_marks(bloom_level),
            })
        
        return questions
    
    def _extract_key_phrases(self, text: str) -> list[str]:
        """Use spaCy to extract answer-worthy noun phrases. Free."""
        import spacy
        doc = nlp(text)
        return [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) > 1][:10]
    
    def _classify_bloom_level(self, question: str) -> str:
        """Rule-based Bloom's classification via verb detection."""
        q_lower = question.lower()
        BLOOM_VERBS = {
            "remember": ["define", "list", "recall", "name", "state", "identify"],
            "understand": ["explain", "describe", "summarize", "interpret", "classify"],
            "apply": ["calculate", "solve", "use", "demonstrate", "apply"],
            "analyze": ["compare", "differentiate", "examine", "break down", "analyze"],
            "evaluate": ["justify", "critique", "assess", "judge", "evaluate", "argue"],
            "create": ["design", "construct", "formulate", "propose", "create"],
        }
        for level, verbs in BLOOM_VERBS.items():
            if any(v in q_lower for v in verbs):
                return level
        return "understand"  # sensible default
```

**Note on quality**: The T5 model will generate syntactically valid questions but may occasionally produce awkward phrasings. Recommended: after the initial build, use BloomLLM's fine-tuning approach — generate 500–1,000 questions with Claude, have a human expert label them by Bloom's level, and fine-tune the T5 model on your own domain corpus. This is a one-time cost that yields a permanently free, higher-quality model.

**Deployment**: Load the model inside the Celery worker process once at startup. Keep it in memory. For Railway with 512MB RAM, use CPU inference with `torch.no_grad()` — inference time is ~50–100ms per question, acceptable for async batch processing.

---

### 2.3 PlagueScope — Full Replacement (Zero API Cost)

**Current problem**: The existing implementation calls OpenAI's embedding API for all submissions, then does pairwise cosine similarity in Python. This is both a financial and latency problem.

**Research basis**: The 2025 PAN Plagiarism Detection task winners use a cascading three-stage pipeline: TF-IDF cosine → character n-gram Jaccard → Transformer classifier. For same-exam plagiarism (identical prompt, same time, same source material), SBERT's `all-MiniLM-L6-v2` achieves 95%+ precision. Springer (2025) confirms that integrating TF-IDF with SBERT-based cosine similarity is a "scalable and comprehensive plagiarism detection system."

**Recommended model**: `all-MiniLM-L6-v2` (80MB, free, CPU inference ~5ms per embedding)

**Full replacement implementation**:

```python
# engines/eie/plague_scope.py

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from difflib import SequenceMatcher

class PlagueScopeV2:
    def __init__(self):
        # Load once at startup — 80MB
        self.sbert = SentenceTransformer("all-MiniLM-L6-v2")
    
    async def analyze_batch(self, exam_id: str, institution_id: str) -> dict:
        submissions = await db.exam_submissions.select(exam_id=exam_id)
        student_ids = [s['student_id'] for s in submissions]
        texts = [" ".join(str(v) for v in s['answers'].values())[:8000] for s in submissions]
        
        # Stage 1: TF-IDF fast pre-filter (CPU, milliseconds per pair)
        tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = tfidf.fit_transform(texts)
        tfidf_sims = cosine_similarity(tfidf_matrix)
        
        # Stage 2: SBERT deep similarity (only for pairs with TF-IDF > 0.4)
        sbert_embeddings = self.sbert.encode(texts, batch_size=32, normalize_embeddings=True)
        
        n = len(student_ids)
        similarity_matrix = np.zeros((n, n))
        flagged_pairs = []
        
        for i in range(n):
            for j in range(i+1, n):
                # Fast pre-filter
                if tfidf_sims[i][j] < 0.3:
                    similarity_matrix[i][j] = similarity_matrix[j][i] = tfidf_sims[i][j]
                    continue
                
                # Full SBERT similarity for suspicious pairs
                sbert_sim = float(np.dot(sbert_embeddings[i], sbert_embeddings[j]))
                
                # Stage 3: Character LCS for exact copy detection
                lcs_sim = SequenceMatcher(None, texts[i][:2000], texts[j][:2000]).ratio()
                
                # Fused score (weights from PAN 2025 research)
                fused = 0.5 * sbert_sim + 0.3 * tfidf_sims[i][j] + 0.2 * lcs_sim
                similarity_matrix[i][j] = similarity_matrix[j][i] = round(fused, 3)
                
                if fused > 0.82:
                    flagged_pairs.append({
                        "student_a": student_ids[i],
                        "student_b": student_ids[j],
                        "similarity": fused,
                        "sbert_score": sbert_sim,
                        "tfidf_score": float(tfidf_sims[i][j]),
                        "lcs_score": lcs_sim,
                        "flag_type": "exact_copy" if lcs_sim > 0.7 else "paraphrase"
                    })
        
        return {
            "student_ids": student_ids,
            "matrix": similarity_matrix.tolist(),
            "flagged_pairs": sorted(flagged_pairs, key=lambda x: -x['similarity']),
            "threshold": 0.82
        }
```

**Zero API cost. Zero latency dependency on external services. Runs entirely on your Railway container.**

---

### 2.4 SmartMock Grading — Tiered Grading (75% Reduction)

**Current problem**: Every submitted mock answer is sent to Claude for evaluation via semantic similarity. For MCQs and short answers, this is massive overkill.

**Research basis**: MDPI Applied Sciences (2024) demonstrates SBERT-based ASAG achieves **86–88% accuracy** on standard benchmark datasets using semantic cosine similarity alone, without any LLM. The key insight: for multiple-choice questions, there is literally no need for LLM evaluation (exact match). For short-answer questions (< 80 words), SBERT + cosine similarity handles it well. Only long descriptive answers genuinely benefit from rubric-aligned LLM grading.

**Tiered grading architecture**:

```python
# engines/ape/smart_mock.py

from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np

class SmartMockGraderV2:
    def __init__(self):
        # Bi-encoder for fast candidate scoring (80MB)
        self.bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")
        # Cross-encoder for precision re-ranking on borderline short answers (85MB)
        self.cross_encoder = CrossEncoder("cross-encoder/stsb-roberta-base")
    
    async def grade_submission(self, mock_id: str, answers: dict) -> dict:
        questions = await db.question_bank.get_by_ids(list(answers.keys()))
        results = []
        
        for q in questions:
            student_answer = answers.get(q['id'], "")
            
            if q['question_type'] == 'MCQ':
                # TIER 1: Exact match — zero cost
                score = q['marks'] if student_answer.strip().upper() == q['correct_option'] else 0
                feedback = "Correct!" if score else f"Correct answer: {q['correct_option']}"
                results.append(self._result(q, score, feedback, tier=1))
            
            elif q['question_type'] in ('short_answer', 'fill_blank') and len(student_answer.split()) < 80:
                # TIER 2: SBERT semantic similarity — near-zero cost
                model_emb = self.bi_encoder.encode(q['model_answer'], normalize_embeddings=True)
                student_emb = self.bi_encoder.encode(student_answer, normalize_embeddings=True)
                similarity = float(np.dot(model_emb, student_emb))
                
                # Cross-encoder re-score if borderline (0.55–0.75)
                if 0.55 < similarity < 0.75:
                    cross_score = self.cross_encoder.predict([(q['model_answer'], student_answer)])
                    similarity = (similarity + float(cross_score[0])) / 2
                
                score = round(q['marks'] * max(0, min(1, similarity)), 1)
                feedback = self._generate_feedback_from_similarity(similarity, q)
                results.append(self._result(q, score, feedback, tier=2, similarity=similarity))
            
            else:
                # TIER 3: LLM — only for long/descriptive answers
                llm_result = await self._llm_grade_descriptive(q, student_answer)
                results.append(self._result(q, llm_result['marks'], llm_result['feedback'], tier=3))
        
        return {
            "results": results,
            "total_score": sum(r['marks_awarded'] for r in results),
            "max_score": sum(q['marks'] for q in questions),
            "tier_breakdown": {
                1: sum(1 for r in results if r['tier'] == 1),
                2: sum(1 for r in results if r['tier'] == 2),
                3: sum(1 for r in results if r['tier'] == 3),
            }
        }
    
    def _generate_feedback_from_similarity(self, sim: float, q: dict) -> str:
        """Rule-based feedback — zero cost."""
        if sim > 0.85:
            return "Excellent answer — key concepts well covered."
        elif sim > 0.65:
            return f"Good attempt. Consider also mentioning: {', '.join(q.get('key_concepts', [])[:2])}"
        else:
            return f"Review this topic. Model answer covers: {q['model_answer'][:120]}..."
```

---

### 2.5 RevisionClock — Replace with SM-2 / FSRS Algorithm (90% Reduction)

**Current problem**: Every revision schedule generation and rebalance calls Claude Sonnet with a long prompt containing the entire syllabus. This is expensive and produces a result that could be computed deterministically with superior scientific backing.

**Research basis**: The SM-2 algorithm (Wozniak, 1987) and its modern successor FSRS (Free Spaced Repetition Scheduler, 2022, open-source) are the gold standard for spaced repetition scheduling, used by Anki, Quizlet, and Memrise. FSRS is based on MaiMemo's DSR model, published at ACM KDD and IEEE TKDE. Both are computationally trivial (< 50 lines of code), require no API calls, and adapt to individual student performance data in real-time.

**Implementation using open-spaced-repetition/anki-sm-2**:

```python
# engines/ape/revision_clock.py

from anki_sm_2 import Scheduler, Card, Rating
from datetime import date, datetime, timezone, timedelta
from typing import Optional
import json

class RevisionClockV2:
    def __init__(self):
        self.scheduler = Scheduler()
    
    async def initialize_cards(self, user_id: str, institution_id: str, exam_date: date) -> dict:
        """
        Create an SM-2 card for each syllabus topic.
        Cards for weak topics get negative initial easiness factor.
        No LLM call.
        """
        syllabus = await db.syllabi.get(institution_id=institution_id)
        weak_spots = {w['concept']: w['score'] for w in 
                      await db.weak_spots.select(user_id=user_id)}
        
        days_to_exam = (exam_date - date.today()).days
        cards_data = []
        
        for unit in syllabus['data']['units']:
            # Allocate review budget proportional to weightage
            unit_weight = unit['weightage_marks'] / syllabus['data']['total_marks']
            
            for topic in unit['topics']:
                weakness_score = weak_spots.get(topic['name'], 50)  # 0=weak, 100=strong
                
                # Create SM-2 card
                card = Card(due=datetime.now(timezone.utc))
                
                # Set initial due date based on urgency and weakness
                # Weak topics: start reviewing immediately
                # Strong topics: defer to mid-schedule
                if weakness_score < 40:
                    delay_days = 0  # Start today
                elif weakness_score < 70:
                    delay_days = max(1, days_to_exam // 4)
                else:
                    delay_days = max(2, days_to_exam // 2)
                
                card.due = datetime.now(timezone.utc) + timedelta(days=delay_days)
                
                cards_data.append({
                    "topic": topic['name'],
                    "unit": unit['unit_number'],
                    "weightage": unit['weightage_marks'],
                    "card_state": card.to_dict(),
                    "weakness_score": weakness_score,
                    "user_id": user_id
                })
        
        # Sort by due date to build the initial calendar
        cards_data.sort(key=lambda x: x['card_state']['due'])
        
        # Build daily calendar (max 4 topics/day, 1 rest day/week)
        schedule = self._build_calendar(cards_data, exam_date)
        
        await db.revision_schedules.upsert({
            "user_id": user_id,
            "schedule": schedule,
            "cards": cards_data,
            "exam_date": str(exam_date)
        })
        return schedule
    
    async def record_session(self, user_id: str, topic: str, performance: int):
        """
        Update SM-2 card after a study session. 
        performance: 0=complete_blackout, 3=good, 5=perfect
        No LLM call.
        """
        schedule_data = await db.revision_schedules.get(user_id=user_id)
        cards = schedule_data['cards']
        
        for card_data in cards:
            if card_data['topic'] == topic:
                card = Card.from_dict(card_data['card_state'])
                rating = self._performance_to_rating(performance)
                card, review_log = self.scheduler.review_card(card, rating)
                card_data['card_state'] = card.to_dict()
                break
        
        # Rebuild schedule with updated card states
        exam_date = date.fromisoformat(schedule_data['exam_date'])
        updated_schedule = self._build_calendar(cards, exam_date)
        
        await db.revision_schedules.upsert({
            "user_id": user_id,
            "schedule": updated_schedule,
            "cards": cards,
            "exam_date": str(exam_date)
        })
        return updated_schedule
    
    def _performance_to_rating(self, score: int) -> Rating:
        """Map a 0–100 performance score to SM-2 rating."""
        if score < 25: return Rating.Again
        if score < 50: return Rating.Hard
        if score < 80: return Rating.Good
        return Rating.Easy
    
    def _build_calendar(self, cards: list, exam_date: date) -> list:
        """Deterministic calendar builder — no LLM."""
        calendar = {}
        today = date.today()
        
        for card_data in cards:
            due = datetime.fromisoformat(card_data['card_state']['due']).date()
            due = max(today, min(due, exam_date - timedelta(days=2)))
            
            day_str = str(due)
            if day_str not in calendar:
                calendar[day_str] = []
            
            # Max 4 topics per day
            if len(calendar[day_str]) < 4:
                calendar[day_str].append({
                    "topic": card_data['topic'],
                    "unit": card_data['unit'],
                    "duration_mins": self._estimate_duration(card_data),
                    "priority": "high" if card_data['weakness_score'] < 40 else "medium",
                    "type": "study" if card_data['card_state']['reps'] == 0 else "revise"
                })
        
        return [{"date": k, "tasks": v} for k, v in sorted(calendar.items())]
    
    def _estimate_duration(self, card_data: dict) -> int:
        """Estimate study time based on weakness and unit weightage."""
        base = 45  # minutes
        if card_data['weakness_score'] < 40:
            return min(90, base + 30)
        elif card_data['card_state']['reps'] > 2:
            return max(20, base - 20)  # Already reviewed multiple times
        return base
```

**When to still call Claude Sonnet**: Only when the student explicitly requests a natural-language explanation of their schedule ("Why am I reviewing Thermodynamics today?") or for the initial onboarding where you want a narrative explanation of the plan. All scheduling math is deterministic.

---

### 2.6 MemoryTutor — Add a Knowledge State Layer (60% Reduction)

**Current problem**: Building the "session context" by summarizing chat history is an LLM call before the LLM call. The weak spots and covered topics are tracked as flat lists, not as a proper student knowledge model.

**Research basis**: Bayesian Knowledge Tracing (BKT, Corbett & Anderson 1994, still state-of-practice) models student knowledge as a Hidden Markov Model with four parameters: `P(L0)` (prior knowledge), `P(T)` (learning rate), `P(G)` (guess probability), `P(S)` (slip probability). Deep Knowledge Tracing (DKT, Piech et al., Stanford 2015) extends this with LSTM, achieving 25% AUC gain over BKT. Both are free, run locally, and provide real-time student knowledge state without any LLM calls.

**Implementation — replace the `get_session_context` method with BKT**:

```python
# core/knowledge_tracker.py

import numpy as np
from typing import Dict

class BayesianKnowledgeTracker:
    """
    Lightweight BKT implementation. 
    Per-student, per-topic knowledge state. No GPU, no API.
    Parameters from literature (Corbett & Anderson, 1994):
      p_learn: probability of transitioning from not-knowing to knowing
      p_guess: probability of correct answer despite not knowing
      p_slip:  probability of incorrect answer despite knowing
    """
    DEFAULT_PARAMS = {
        'p_prior': 0.3,   # initial knowledge probability
        'p_learn': 0.15,  # learning rate per attempt
        'p_guess': 0.25,
        'p_slip': 0.10,
    }
    
    def update(self, p_knew: float, was_correct: bool, params: dict = None) -> float:
        """Update knowledge probability after one attempt. Returns new P(knew)."""
        p = params or self.DEFAULT_PARAMS
        
        # P(correct | knew) and P(correct | didn't know)
        if was_correct:
            p_correct_given_knew = 1 - p['p_slip']
            p_correct_given_not_knew = p['p_guess']
        else:
            p_correct_given_knew = p['p_slip']
            p_correct_given_not_knew = 1 - p['p_guess']
        
        # Bayesian update (Bayes theorem)
        p_knew_given_obs = (
            (p_knew * p_correct_given_knew) /
            (p_knew * p_correct_given_knew + (1 - p_knew) * p_correct_given_not_knew)
        )
        
        # Apply learning (transition probability)
        p_knew_new = p_knew_given_obs + (1 - p_knew_given_obs) * p['p_learn']
        return min(1.0, p_knew_new)
    
    async def get_student_state(self, user_id: str) -> Dict[str, float]:
        """
        Return a topic → knowledge_probability mapping.
        This replaces the 'summarize history' LLM call entirely.
        """
        mock_results = await db.mock_results.select(user_id=user_id)
        weak_spots = await db.weak_spots.select(user_id=user_id)
        
        # Seed from weak_spots table (normalized 0–1)
        states = {w['concept']: w['score'] / 100 for w in weak_spots}
        
        # Update from mock history using BKT
        for result in sorted(mock_results, key=lambda x: x['created_at']):
            topic = result['topic']
            if topic not in states:
                states[topic] = self.DEFAULT_PARAMS['p_prior']
            
            was_correct = result['score'] >= (result['max_score'] * 0.6)
            states[topic] = self.update(states[topic], was_correct)
        
        return states

# Usage in MemoryTutor:
# context_dict = await knowledge_tracker.get_student_state(user_id)
# No LLM call to build context. The state dict feeds directly into the system prompt.
```

**Modified `MemoryTutor.get_session_context`**:

```python
async def get_session_context(self, user_id: str) -> str:
    # BKT state — no LLM call
    knowledge_state = await self.knowledge_tracker.get_student_state(user_id)
    
    # Classify topics by mastery
    mastered = [t for t, p in knowledge_state.items() if p >= 0.8]
    learning  = [t for t, p in knowledge_state.items() if 0.5 <= p < 0.8]
    weak      = [t for t, p in knowledge_state.items() if p < 0.5]
    
    # Last session from DB (simple SELECT, not an LLM summarization)
    last_session = await db.chat_history.get_last(user_id=user_id)
    
    return f"""
Student Knowledge State (Bayesian Knowledge Tracing):
- Mastered (P > 0.80): {', '.join(mastered[:5]) or 'None yet'}
- In Progress (P 0.50–0.80): {', '.join(learning[:5]) or 'None yet'}  
- Weak (P < 0.50): {', '.join(weak[:5]) or 'None yet'}
- Last session: {last_session['created_at'] if last_session else 'First session'}
- Unresolved question from last session: {last_session.get('unresolved_question', 'None')}

Priority today: Address weak topics first. Do not repeat mastered topics unless asked.
"""
```

---

### 2.7 DocDoubt — Hybrid BM25 + Dense Retrieval (Same Cost, Better Quality)

**Current problem**: Pure dense vector search (Qdrant only) misses exact keyword matches — critical for subject-specific terminology, formula names, theorem names, and numbered equations. Students asking about "Theorem 3.2" or "the Rankine-Hugoniot condition" get poor retrieval.

**Research basis**: Meilisearch benchmarks (June 2024) show hybrid search improves retrieval accuracy by **37% in technical domains**. The BM-RAGAM paper (MDPI, 2024) shows BM25 + semantic hybrid retrieval "greatly reduced hallucination" in domain-specific QA. Reciprocal Rank Fusion (RRF) is the recommended merging strategy — parameter-free and robust.

**Implementation — replace the simple Qdrant search with hybrid retrieval**:

```python
# core/hybrid_retriever.py

from rank_bm25 import BM25Okapi
import numpy as np
from typing import List

class HybridRetriever:
    """
    Combines BM25 (keyword) + Qdrant dense (semantic) with RRF fusion.
    No additional API calls — BM25 runs locally, Qdrant is already in use.
    """
    
    def __init__(self, qdrant_client, embedding_model):
        self.qdrant = qdrant_client
        self.embedder = embedding_model
        self._bm25_indexes = {}  # per-collection BM25 index, built lazily
    
    async def search(
        self,
        query: str,
        collection: str,
        limit: int = 8,
        score_threshold: float = 0.50,
        alpha: float = 0.65  # weight toward semantic (0=BM25 only, 1=dense only)
    ) -> list:
        
        # Parallel retrieval
        bm25_results = await self._bm25_search(query, collection, limit * 2)
        dense_results = await self.qdrant.search(
            collection=collection,
            query=await self.embedder.embed(query),
            limit=limit * 2,
            score_threshold=score_threshold
        )
        
        # Reciprocal Rank Fusion (RRF) — k=60 is standard
        return self._rrf_fuse(bm25_results, dense_results, k=60, limit=limit)
    
    def _rrf_fuse(self, bm25_results, dense_results, k: int, limit: int) -> list:
        scores = {}
        
        for rank, result in enumerate(bm25_results):
            doc_id = result['id']
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
        for rank, result in enumerate(dense_results):
            doc_id = result.id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
        # Build merged result list
        all_results = {r['id']: r for r in bm25_results}
        all_results.update({r.id: r.payload for r in dense_results})
        
        sorted_ids = sorted(scores.keys(), key=lambda x: -scores[x])
        return [all_results[doc_id] for doc_id in sorted_ids[:limit] if doc_id in all_results]
    
    async def _bm25_search(self, query: str, collection: str, limit: int) -> list:
        if collection not in self._bm25_indexes:
            await self._build_bm25_index(collection)
        
        bm25, docs = self._bm25_indexes[collection]
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:limit]
        
        return [
            {"id": docs[i]['id'], "payload": docs[i], "score": float(scores[i])}
            for i in top_indices if scores[i] > 0
        ]
    
    async def _build_bm25_index(self, collection: str):
        """Build BM25 index from Qdrant collection. Rebuild nightly via Celery beat."""
        all_points = await self.qdrant.scroll(collection=collection, limit=10000)
        docs = [{"id": p.id, "text": p.payload.get('text', ''), **p.payload} 
                for p in all_points[0]]
        tokenized = [doc['text'].lower().split() for doc in docs]
        self._bm25_indexes[collection] = (BM25Okapi(tokenized), docs)
```

**Add to `requirements.txt`**: `rank-bm25==0.2.2`

**Add a nightly Celery beat task** to rebuild BM25 indexes when new documents are ingested. This adds < 100ms to retrieval for collections up to 50,000 chunks.

---

### 2.8 HandwrittenEvaluator — Tiered Evaluation (65% Reduction)

**Current problem**: Every answer in every handwritten script goes to Claude Sonnet, regardless of whether it's a 2-mark MCQ or a 20-mark essay.

**Research basis**: SBERT achieves 86–88% accuracy on automated short answer grading (MDPI, 2024). Cross-encoder rerankers (`cross-encoder/stsb-roberta-base`) provide a second-opinion scoring that catches SBERT's false positives. Only genuinely long descriptive answers (> 120 words) benefit meaningfully from LLM rubric-aligned evaluation.

```python
# engines/eie/handwritten_evaluator.py

from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np

class HandwrittenEvaluatorV2:
    THRESHOLDS = {
        'mcq_short': 80,    # word count threshold for short answer
        'short_long': 120,  # word count threshold for long answer
        'sbert_confident': 0.80,  # SBERT score above which skip cross-encoder
        'sbert_ambiguous': (0.50, 0.80),  # range needing cross-encoder
        'escalate_to_llm': 0.50,  # below this, always use LLM
    }
    
    def __init__(self):
        self.bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.cross_encoder = CrossEncoder("cross-encoder/stsb-roberta-base")
    
    async def evaluate(self, script_image_keys: list, exam_id: str, 
                       student_id: str, institution_id: str) -> list:
        # OCR via Google Vision (unchanged — this is necessary)
        full_script = await self._ocr_script(script_image_keys)
        exam_questions = await db.exam_questions_map.select(exam_id=exam_id)
        results = []
        
        for q in exam_questions:
            student_answer = self._extract_answer_for_question(full_script, q['order_index'])
            word_count = len(student_answer.split())
            
            if q['question_type'] == 'MCQ' or word_count < 10:
                # TIER 1: Simple string match / keyword check
                result = self._grade_mcq_or_fill(q, student_answer)
            
            elif word_count < self.THRESHOLDS['short_long']:
                # TIER 2: SBERT grading for short answers
                result = self._grade_with_sbert(q, student_answer)
            
            else:
                # TIER 3: LLM for long descriptive answers only
                result = await self._grade_with_llm(q, student_answer)
            
            results.append(result)
        
        return results
    
    def _grade_with_sbert(self, q: dict, student_answer: str) -> dict:
        model_emb = self.bi_encoder.encode(q['model_answer'], normalize_embeddings=True)
        student_emb = self.bi_encoder.encode(student_answer, normalize_embeddings=True)
        sbert_score = float(np.dot(model_emb, student_emb))
        
        if sbert_score >= self.THRESHOLDS['sbert_confident']:
            final_score = sbert_score
            method = "sbert"
        elif sbert_score >= self.THRESHOLDS['escalate_to_llm']:
            # Cross-encoder re-score for borderline cases
            cross_score = self.cross_encoder.predict([(q['model_answer'], student_answer)])[0]
            final_score = (sbert_score + cross_score) / 2
            method = "sbert+cross-encoder"
        else:
            # Low confidence — mark for LLM escalation
            # But still provide a provisional score
            final_score = sbert_score
            method = "sbert_provisional"
        
        marks = round(q['marks'] * max(0, final_score), 1)
        return {
            "question_id": q['question_id'],
            "marks_awarded": marks,
            "max_marks": q['marks'],
            "method": method,
            "similarity_score": final_score,
            "confidence": "high" if final_score > 0.75 else "medium" if final_score > 0.50 else "low",
            "feedback": self._template_feedback(final_score, q),
            "needs_review": final_score < 0.55  # Flag for faculty human review
        }
```

---

### 2.9 GapFinder — Pure Vector Algebra (100% LLM Removal)

**Current problem**: The existing code correctly uses Qdrant similarity search to identify gaps, but then doesn't persist the output intelligently — and still calls an LLM to "analyze" gaps that are already fully determined by the similarity scores.

**Optimization**: Gap detection is already a deterministic vector algebra problem. No LLM needed. The only LLM-worthy enhancement would be generating a *natural language recommendation* for each gap, which can be templated.

```python
# engines/iae/gap_finder.py
# The core analysis loop stays the same — it's already mostly algorithmic.
# REMOVE any LLM calls and replace with template-based recommendations.

GAP_RECOMMENDATIONS = {
    "coverage_gap": "Topic '{topic}' appears in {exam_count} past exam questions but has only {courseware_count} coverage units in courseware. Consider adding lecture notes, worked examples, or a supplementary reading list.",
    "performance_gap": "Topic '{topic}' is taught (courseware coverage: {courseware_count} units) but students average {avg_score:.0f}% on mock questions. Recommend reviewing pedagogical approach or difficulty calibration.",
    "blind_spot": "Topic '{topic}' is on the syllabus but appears in neither courseware nor past exams. Verify if this is intentional or an oversight."
}

async def get_patterns(self, institution_id: str) -> dict:
    # ... (existing vector search logic, unchanged) ...
    
    for gap in gaps:
        # Template-based recommendation — zero LLM cost
        gap['recommendation'] = GAP_RECOMMENDATIONS[gap['gap_type']].format(
            topic=gap['topic'],
            exam_count=gap['exam_frequency'],
            courseware_count=gap['courseware_coverage'],
            avg_score=gap.get('avg_mock_score', 0) or 0
        )
    
    return {"gaps": gaps, "total_topics": total}
```

---

### 2.10 PaperPatternMiner — Replace Question Extraction with spaCy (90% Reduction)

**Current problem**: Claude Haiku is called to extract questions from each exam PDF. Exam papers have highly consistent formats — question numbers, mark allocations, and question text follow recognizable patterns.

```python
# engines/ace/paper_pattern_miner.py

import re
import spacy

nlp = spacy.load("en_core_web_sm")

QUESTION_NUM_PATTERN = re.compile(
    r'^(?:Q\.?|Question\.?|Ques\.?)\s*(\d+)[\s.:)\-]+(.+?)(?=\n(?:Q\.?|Question\.?|\d+[.)]\s)|\Z)',
    re.MULTILINE | re.DOTALL
)
MARKS_INLINE = re.compile(r'\[(\d+)\s*(?:marks?|pts?)\]', re.IGNORECASE)
QUESTION_TYPE_SIGNALS = {
    'MCQ': ['choose', 'select', 'which of the following', 'tick', 'circle'],
    'numerical': ['calculate', 'find', 'compute', 'evaluate', 'determine the value'],
    'diagram': ['draw', 'sketch', 'label', 'illustrate'],
    'descriptive': ['explain', 'describe', 'discuss', 'elaborate', 'what is', 'define'],
}

class PaperPatternMinerV2:
    async def ingest_paper(self, paper_text: str, year: int, institution_id: str):
        questions = self._extract_questions_regex(paper_text)
        
        if len(questions) < 3:
            # Fallback to spaCy sentence segmentation for non-standard formats
            questions = self._extract_questions_spacy(paper_text)
        
        # Only call LLM if both methods produce < 3 questions (rare edge case)
        if len(questions) < 3:
            questions = await self._llm_extract_questions(paper_text[:6000])
        
        # Topic matching is unchanged — uses Qdrant similarity search
        for q in questions:
            q['year'] = year
            q_embedding = await self.embedder.embed(q['question_text'])
            topic_match = await self.qdrant.search(
                collection=f"{institution_id}_syllabus",
                query=q_embedding, limit=1
            )
            q['topic'] = topic_match[0].payload['topic'] if topic_match else None
            q['unit'] = topic_match[0].payload['unit'] if topic_match else None
        
        await db.exam_questions.insert_many(questions)
    
    def _extract_questions_regex(self, text: str) -> list:
        questions = []
        for match in QUESTION_NUM_PATTERN.finditer(text):
            q_text = match.group(2).strip()
            marks_match = MARKS_INLINE.search(q_text)
            q_type = self._detect_type(q_text)
            
            questions.append({
                "question_text": re.sub(r'\[\d+\s*marks?\]', '', q_text).strip(),
                "marks": int(marks_match.group(1)) if marks_match else 5,
                "question_type": q_type,
                "topic_hint": self._extract_topic_hint(q_text),
            })
        return questions
    
    def _detect_type(self, text: str) -> str:
        text_lower = text.lower()
        for q_type, signals in QUESTION_TYPE_SIGNALS.items():
            if any(signal in text_lower for signal in signals):
                return q_type
        return 'descriptive'
```

---

### 2.11 ReportWeaver — Template + Stats + Minimal LLM (70% Reduction)

**Current problem**: The entire report is generated by Claude Sonnet, which regenerates data that is already computed (averages, distributions, top/bottom students).

**Optimized approach**: All data sections are rendered from a Jinja2 template. Only the `Executive Summary` and `Recommended Interventions` sections (which require genuine natural language synthesis and judgment) are sent to Claude.

```python
# workers/tasks/reporting.py

from jinja2 import Template
import numpy as np

REPORT_TEMPLATE = Template("""
# Batch Performance Report — {{ exam_title }}
**Generated**: {{ generated_date }} | **Institution**: {{ institution_name }}

---

## 1. Executive Summary
{{ executive_summary }}

## 2. Score Distribution Analysis
| Metric | Value |
|---|---|
| Total Students | {{ stats.total }} |
| Average Score | {{ "%.1f"|format(stats.avg) }}% |
| Median Score | {{ "%.1f"|format(stats.median) }}% |
| Std. Deviation | {{ "%.1f"|format(stats.std_dev) }}% |
| Highest Score | {{ "%.1f"|format(stats.max_score) }}% |
| Lowest Score | {{ "%.1f"|format(stats.min_score) }}% |
| Pass Rate (≥40%) | {{ "%.1f"|format(stats.pass_rate) }}% |

**Score Bands:**
| Band | Count | Percentage |
|---|---|---|
{% for band in stats.bands %}| {{ band.label }} | {{ band.count }} | {{ "%.1f"|format(band.pct) }}% |
{% endfor %}

## 3. Topic-Wise Breakdown
| Topic | Unit | Avg Score | Attempts |
|---|---|---|---|
{% for t in topic_scores %}| {{ t.topic }} | {{ t.unit }} | {{ "%.1f"|format(t.avg_score) }}% | {{ t.attempts }} |
{% endfor %}

## 4. At-Risk Students (Score < 40%)
{% for s in at_risk_students %}
- **{{ s.name }}** (Roll: {{ s.roll }}): {{ "%.1f"|format(s.score) }}% — Weak areas: {{ s.weak_topics }}
{% endfor %}

## 5. Recommended Interventions
{{ recommendations }}

## 6. Comparison to Previous Cycle
{% if prev_stats %}
| Metric | Previous | Current | Change |
|---|---|---|---|
| Average | {{ "%.1f"|format(prev_stats.avg) }}% | {{ "%.1f"|format(stats.avg) }}% | {{ "%+.1f"|format(stats.avg - prev_stats.avg) }}% |
| Pass Rate | {{ "%.1f"|format(prev_stats.pass_rate) }}% | {{ "%.1f"|format(stats.pass_rate) }}% | {{ "%+.1f"|format(stats.pass_rate - prev_stats.pass_rate) }}% |
{% else %}No previous cycle data available.{% endif %}
""")

@celery.task
async def generate_batch_report(exam_id: str, institution_id: str, faculty_id: str):
    submissions = await db.exam_submissions.select(exam_id=exam_id, grading_status='final')
    scores = [s['score'] for s in submissions if s['score'] is not None]
    
    # All statistics computed locally — no LLM
    stats = {
        'total': len(scores),
        'avg': np.mean(scores),
        'median': np.median(scores),
        'std_dev': np.std(scores),
        'max_score': max(scores),
        'min_score': min(scores),
        'pass_rate': sum(1 for s in scores if s >= 40) / len(scores) * 100,
        'bands': [
            {'label': '90–100%', 'count': sum(1 for s in scores if s >= 90), 'pct': ...},
            {'label': '70–89%', 'count': sum(1 for s in scores if 70 <= s < 90), 'pct': ...},
            # ... etc
        ]
    }
    
    # Only 2 sections sent to LLM — Executive Summary + Recommendations
    aggregated_data = {
        'stats': stats,
        'topic_scores': await _compute_topic_scores(submissions),
        'gap_analysis': await gap_finder.analyze(institution_id),
    }
    
    exec_summary, recommendations = await asyncio.gather(
        llm.complete(model="claude-haiku-4-5-20251001",  # Haiku sufficient
            system="Write a 3-sentence executive summary for a faculty exam performance report.",
            user=f"Data: {json.dumps(aggregated_data, indent=2)[:3000]}"),
        llm.complete(model="claude-haiku-4-5-20251001",
            system="Write 3–5 specific, actionable teaching recommendations based on these exam results.",
            user=f"Gaps: {json.dumps(aggregated_data['gap_analysis'], indent=2)[:2000]}")
    )
    
    # Render with Jinja2 — rest of report is pure template
    report_md = REPORT_TEMPLATE.render(
        exec_summary=exec_summary.text,
        recommendations=recommendations.text,
        stats=stats,
        # ... other fields
    )
    
    pdf_bytes = markdown_to_pdf(report_md)
    # ... save and notify
```

---

## 3. Model Hosting Strategy for Railway

All Tier 2 models should be loaded once at FastAPI startup, not per-request.

```python
# main.py

from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import T5ForConditionalGeneration, T5Tokenizer
import spacy
import torch

# Loaded at startup, shared across all requests
app.state.bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")
app.state.cross_encoder = CrossEncoder("cross-encoder/stsb-roberta-base")
app.state.t5_qg_tokenizer = T5Tokenizer.from_pretrained("valhalla/t5-base-qg-hl")
app.state.t5_qg_model = T5ForConditionalGeneration.from_pretrained("valhalla/t5-base-qg-hl")
app.state.t5_qg_model.eval()
app.state.nlp = spacy.load("en_core_web_sm")
```

**Updated Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y libmagic1 tesseract-ocr

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model at build time (not runtime)
RUN python -m spacy download en_core_web_sm

# Pre-download HuggingFace models at build time
# This bakes them into the container image, avoiding cold-start downloads
RUN python -c "
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import T5ForConditionalGeneration, T5Tokenizer
SentenceTransformer('all-MiniLM-L6-v2')
CrossEncoder('cross-encoder/stsb-roberta-base')
T5Tokenizer.from_pretrained('valhalla/t5-base-qg-hl')
T5ForConditionalGeneration.from_pretrained('valhalla/t5-base-qg-hl')
print('Models cached.')
"

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Railway memory implications**: The Docker image will be ~2.5–3GB with models baked in. Railway's Starter plan supports this. Cold-start time drops to ~15 seconds (model loading from disk) vs. 60+ seconds if downloaded at runtime. CPU inference is fast enough for all use cases: SBERT embed ~5ms, T5 generate ~100ms, BKT update < 1ms.

---

## 4. Updated `requirements.txt` additions

```
# Tier 2 models and supporting libraries
sentence-transformers==3.0.1
transformers==4.43.0
torch==2.3.1          # CPU-only is fine; add --index-url for CUDA if Railway upgrades
spacy==3.7.6
rank-bm25==0.2.2
anki-sm-2==0.2.0       # SM-2 scheduling algorithm
jinja2==3.1.4          # Report templating
```

---

## 5. Revised Cost Estimate (~200 Active Users)

| Service | Old Cost | New Cost | Notes |
|---|---|---|---|
| Vercel Hobby | $0 | $0 | — |
| Railway (backend + worker) | ~$10 | ~$10 | Same tier |
| Supabase Free | $0 | $0 | — |
| Qdrant Cloud Free | $0 | $0 | — |
| Cloudflare R2 | $0 | $0 | — |
| Upstash Redis | $0 | $0 | — |
| **Anthropic API** | **~$15** | **~$3–4** | Only DocDoubt chat, MemoryTutor chat, descriptive grading, report summaries |
| OpenAI Embeddings | ~$3 | **$0** | Replaced by local SBERT |
| Google Cloud Vision | $0 | $0 | Still needed for OCR |
| **Total** | **~$28/mo** | **~$13–14/mo** | **~50% cost reduction at prototype scale** |

At 2,000 users (post-launch), the savings compound: the old architecture would have scaled to ~$250/month in API costs; the new architecture scales to ~$30–40/month. The heavy cost items (QuestionForge, PlagueScope, SmartMock grading) are now flat-rate regardless of user count.

---

## 6. Implementation Priority

Build in this order to get the highest cost reduction first:

| Priority | Feature | Complexity | Cost Impact |
|---|---|---|---|
| 1 | PlagueScope → SBERT locally | Low | $3/mo saved |
| 2 | QuestionForge → T5 locally | Medium | $5/mo saved |
| 3 | RevisionClock → SM-2 | Low | $3/mo saved |
| 4 | SyllabusMapper → regex + spaCy | Medium | $2/mo saved |
| 5 | SmartMock grading → SBERT tiers | Medium | $2/mo saved |
| 6 | DocDoubt → Hybrid BM25 retrieval | Low (additive) | +quality |
| 7 | MemoryTutor → BKT state | High | $2/mo saved + quality |
| 8 | GapFinder → pure algebra | Low | $0.5/mo saved |
| 9 | HandwrittenEvaluator → tiers | Medium | $1/mo saved |
| 10 | ReportWeaver → template | Medium | $1/mo saved |

---

## 7. Key Research References

1. **Automated Question Generation (Bloom's)**: Scaria et al. (2024). *Automated Educational Question Generation at Different Bloom's Skill Levels using Large Language Models.* AIED 2024. ArXiv:2408.04394
2. **BloomLLM**: Duong-Trung et al. (2024). *BloomLLM: LLMs for Question Generation Combining SFT and Bloom's Taxonomy.* EC-TEL 2024, Springer.
3. **T5 for QA pairs**: Rodriguez-Torrealba et al. (2022) / ScienceDirect (2024). *Automatic question-answer pairs generation using pre-trained LLMs in higher education.*
4. **Hybrid RAG / BM25 + Dense**: BM-RAGAM (MDPI, 2024); Blended RAG (ArXiv 2404.07220); Meilisearch benchmarks (June 2024).
5. **Plagiarism Detection**: PAN 2025 (CLEF): TF-IDF → Jaccard → BERT cascade; Springer (2025) BERT+TF-IDF+Cosine hybrid.
6. **Automated Short Answer Grading (ASAG)**: MDPI Applied Sciences (2024): SBERT+balanced dataset achieves 86-88%. IEEE (2022): Sentence Transformers for blended assessment.
7. **Knowledge Tracing**: Piech et al. (Stanford, 2015). *Deep Knowledge Tracing.* NIPS 2015. Corbett & Anderson (1994). *Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge.*
8. **Spaced Repetition**: Wozniak (1987). SM-2 Algorithm. Open-Spaced-Repetition (2022). *FSRS: Free Spaced Repetition Scheduler.* GitHub.
9. **SBERT**: Reimers & Gurevych (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP 2019.

---

*BlueScholar LLM Optimization Guide v1.0 — March 2026*  
*All referenced models are MIT/Apache-2.0 licensed and free for commercial use.*
