import express from 'express';
import path from 'path';
import dotenv from 'dotenv';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI } from '@google/genai';

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Lazy-initialized Gemini instance
let aiClient: GoogleGenAI | null = null;
function getGeminiClient(): GoogleGenAI | null {
  if (!aiClient && process.env.GEMINI_API_KEY) {
    aiClient = new GoogleGenAI({
      apiKey: process.env.GEMINI_API_KEY,
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build',
        },
      },
    });
  }
  return aiClient;
}

// Health endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// Gemini AI Lesson Assistant Endpoint
app.post('/api/ai/ask-lesson', async (req, res) => {
  try {
    const { courseTitle, lessonTitle, lessonDescription, question, history } = req.body;

    if (!question || typeof question !== 'string') {
      return res.status(400).json({ error: 'Savol matni kiritilmadi' });
    }

    const ai = getGeminiClient();

    if (!ai) {
      // In case GEMINI_API_KEY is not provided yet, give a smart contextual fallback
      return res.json({
        answer: `BilimGo AI Ustoz (Namuna):\n\nSiz **"${lessonTitle || 'Dars'}"** mavzusi bo'yicha savol berdingiz:\n*"${question}"*\n\n📌 **Asosiy tushuntirish:** Ushbu mavzu bo'yicha dars videosida keltirilgan asosiy tushunchalar va amaliyotlarni ko'rib chiqing. Savolingiz to'liq va mukammal javob olishi uchun tizimda Gemini API sozlanishi faol bo'lishi kifoya.`,
      });
    }

    const systemInstruction = `Siz "BilimGo" o'quv platformasining do'stona, bilimdon va aniq tushuntirib beruvchi AI Ustozisiz (AI Tutor).
Foydalanuvchi hozirda quyidagi darsni o'rganmoqda:
- Kurs: "${courseTitle || 'Dasturlash / Kurs'}"
- Dars nomi: "${lessonTitle || 'Joriy dars'}"
- Dars tavsifi: "${lessonDescription || 'Ushbu darsning amaliy va nazariy qismi'}"

Sizning vazifangiz:
1. O'quvchi dars davomida tushunmagan joylarini so'raganda o'zbek tilida juda sodda, ravon, qiziqarli va professional tilda tushuntirib bering.
2. Agar savol dasturlash yoki texnik mavzuda bo'lsa, ixcham kod parchalari, qadam-baqadam izohlar yoki hayotiy o'xshatishlar keltiring.
3. Javoblarni chiroyli formatda (Markdown va toza HTML teglari: <b>, <code>, <pre>, <ul>, <li>, <table> va h.k.) yozing. HTML teglari kiritilsa yoki so'ralsa, ularni to'g'ri va xavfsiz ko'rinishda taqdim eting.
4. Javobingiz o'quvchini ilhomlantirsin va mavzuni chuqur anglashiga yordam bersin.`;

    let prompt = `O'quvchining savoli: "${question}"\n\nIltimos, ushbu dars kontekstidan kelib chiqib o'quvchiga batafsil va tushunarli javob bering.`;

    if (Array.isArray(history) && history.length > 0) {
      const historyContext = history
        .map((h: { sender: string; text: string }) => `${h.sender === 'user' ? 'O\'quvchi' : 'AI Ustoz'}: ${h.text}`)
        .join('\n');
      prompt = `Oldingi suhbat:\n${historyContext}\n\nO'quvchining yangi savoli: "${question}"\n\nIltimos, dars kontekstida javob bering.`;
    }

    const response = await ai.models.generateContent({
      model: 'gemini-3.7-flash',
      contents: prompt,
      config: {
        systemInstruction,
      },
    });

    const answer = response.text || 'Kechirasiz, javobni shakllantirishda noaniqlik yuz berdi. Iltimos, savolingizni qayta yozib ko\'ring.';
    return res.json({ answer });
  } catch (error: any) {
    console.error('Error generating AI lesson answer:', error);
    return res.status(500).json({
      error: error.message || 'AI xizmati bilan bog\'lanishda xatolik yuz berdi',
    });
  }
});

// Vite & Static middleware setup
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true, host: '0.0.0.0', port: PORT },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`BilimGo Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
