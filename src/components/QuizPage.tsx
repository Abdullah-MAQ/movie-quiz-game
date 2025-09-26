import { useState, useEffect } from "react";
import { GameCard } from "./GameCard";
import { GameButton } from "./GameButton";
import { GameHeader } from "./GameHeader";
import { Progress } from "@/components/ui/progress";
import { Clock, Star, Trophy, AlertCircle } from "lucide-react";
import { API_CONFIG } from "@/lib/config";

const API_BASE = `${API_CONFIG.BASE_URL}/api`;

interface QuestionPayload {
  id: string;
  question: string;
  options: string[];
  difficulty?: string;
  number: number;
  total: number;
}

interface StartResponse {
  session_id: string;
  question: QuestionPayload;
  score: number;
  questions_remaining: number;
}

interface AnswerResponse {
  correct: boolean;
  correct_index: number;
  score: number;
  quiz_complete: boolean;
  next_question?: QuestionPayload;
  difficulty_level?: number;
  questions_remaining?: number;
}

interface UserData {
  user_id: string;
  email: string;
  preferred_genre: string;
}

interface QuizPageProps {
  userData?: UserData | null;
  onNavigate?: (page: string) => void;
}

export function QuizPage({ userData, onNavigate }: QuizPageProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<QuestionPayload | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30);
  const [isAnswered, setIsAnswered] = useState(false);
  const [quizComplete, setQuizComplete] = useState(false);
  const [difficultyLevel, setDifficultyLevel] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [isTimeout, setIsTimeout] = useState(false);

  // Start quiz on mount
  useEffect(() => {
    const start = async () => {
      try {
        setLoading(true);
        const requestBody: any = { total_questions: 10 };
        if (userData?.user_id) {
          requestBody.user_id = userData.user_id;
        }
        const res = await fetch(`${API_BASE}/quiz/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestBody) });
        const data: StartResponse = await res.json();
        setSessionId(data.session_id);
        setQuestion(data.question);
        setScore(data.score);
        setTimeLeft(30);
        setIsAnswered(false);
        setIsTimeout(false);
        setSelectedAnswer(null);
      } catch (e) {
        console.error('Failed to start quiz', e);
      } finally {
        setLoading(false);
      }
    };
    start();
  }, [userData]);

  useEffect(() => {
    if (timeLeft > 0 && !isAnswered && !quizComplete) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && !isAnswered && question) {
      handleTimeout();
    }
  }, [timeLeft, isAnswered, quizComplete, question]);

  const handleAnswerSelect = async (answerIndex: number) => {
    if (isAnswered || !question || !sessionId) return;
    setSelectedAnswer(answerIndex);
    setIsAnswered(true);
    try {
      const res = await fetch(`${API_BASE}/quiz/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
            question_id: question.id,
            answer_index: answerIndex,
            time_left: timeLeft
        })
      });
      const data: AnswerResponse = await res.json();
      console.log('Answer response data:', data);
      setScore(data.score);
      if (data.difficulty_level) setDifficultyLevel(data.difficulty_level);
      if (data.quiz_complete) {
        console.log('Quiz complete, finishing...');
        setQuizComplete(true);
        // Call completion endpoint to save final score
        await completeQuiz(data.score);
      } else if (data.next_question) {
        console.log('Setting next question:', data.next_question);
        // Store the next question for the user to navigate to
        (window as any).__nextQuestion = data.next_question;
      }
      // Store server correctness in question object for styling
      (window as any).__lastCorrectIndex = data.correct_index;
      console.log('Next question stored in window:', (window as any).__nextQuestion);
    } catch (e) {
      console.error('Answer submission failed', e);
    }
  };

  const completeQuiz = async (finalScore: number) => {
    if (!sessionId) return;
    
    try {
      // Calculate quiz stats for completion
      const correctAnswers = 1; // This should be tracked throughout the quiz
      const totalQuestions = 10; // Default value, should come from session
      
      await fetch(`${API_BASE}/quiz/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          final_score: finalScore,
          correct_answers: correctAnswers,
          total_questions: totalQuestions
        })
      });
    } catch (e) {
      console.error('Failed to complete quiz', e);
    }
  };

  const handleTimeout = async () => {
    if (isAnswered || !question || !sessionId) return;
    
    setIsAnswered(true);
    setSelectedAnswer(null);
    setIsTimeout(true);
    
    // Submit timeout as an incorrect answer (index -1 or a default incorrect index)
    try {
      const res = await fetch(`${API_BASE}/quiz/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: question.id,
          answer_index: -1, // Indicate timeout
          time_left: 0
        })
      });
      const data: AnswerResponse = await res.json();
      setScore(data.score);
      if (data.difficulty_level) setDifficultyLevel(data.difficulty_level);
      if (data.quiz_complete) {
        setQuizComplete(true);
        await completeQuiz(data.score);
      } else if (data.next_question) {
        // Store the next question data for the Next Question button
        (window as any).__nextQuestion = data.next_question;
      }
      // Store server correctness for styling (will show correct answer)
      (window as any).__lastCorrectIndex = data.correct_index;
    } catch (e) {
      console.error('Timeout submission failed', e);
      // Fallback: still show next question button if we have stored data
    }
  };

  const nextQuestion = () => {
    const nextQ = (window as any).__nextQuestion as QuestionPayload | undefined;
    console.log('nextQuestion called, nextQ:', nextQ);
    if (!nextQ) {
      console.log('No next question available!');
      return;
    }
    setQuestion(nextQ);
    setSelectedAnswer(null);
    setIsAnswered(false);
    setIsTimeout(false);
    setTimeLeft(30);
    console.log('Successfully loaded next question');
  };

  const restartQuiz = () => {
    // Hard reload to start a fresh session
    window.location.reload();
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8"><p className="text-foreground">Loading quiz...</p></div>;
  }

  if (quizComplete) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <GameCard variant="success" className="p-8 text-center">
            <Trophy className="w-16 h-16 mx-auto mb-4 text-success animate-bounce-in" />
            <h2 className="text-3xl font-bold mb-4 text-foreground">Quiz Complete!</h2>
            <p className="text-xl mb-6 text-muted-foreground">
              Your final score: <span className="text-success font-bold">{score} points</span>
            </p>
            <div className="space-y-4">
              <GameButton variant="primary" size="lg" onClick={restartQuiz}>
                Play Again
              </GameButton>
              <GameButton 
                variant="secondary" 
                size="lg" 
                className="ml-4"
                onClick={() => onNavigate?.("leaderboard")}
              >
                View Leaderboard
              </GameButton>
            </div>
          </GameCard>
        </div>
      </div>
    );
  }
  if (!question) {
    return <div className="container mx-auto px-4 py-8"><p className="text-foreground">No question loaded.</p></div>;
  }

  const progress = (question.number / question.total) * 100;
  const correctIndex = (window as any).__lastCorrectIndex as number | undefined;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Quiz Progress */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <span className="text-muted-foreground">
              Question {question.number} of {question.total}
            </span>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Star className="w-5 h-5 text-warning" />
                <span className="text-foreground font-bold">{score}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-destructive" />
                <span className={`font-bold ${timeLeft <= 10 ? 'text-destructive' : 'text-foreground'}`}>
                  {timeLeft}s
                </span>
              </div>
              <div className="text-sm text-muted-foreground">Diff: {difficultyLevel}</div>
            </div>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Question Card */}
        <GameCard variant="glow" className="p-8 mb-8">
          <div className="mb-6">
            <span className="inline-block px-3 py-1 bg-accent/20 text-accent rounded-full text-sm mb-4">
              {question.difficulty ? question.difficulty : 'Movie'}
            </span>
            <h2 className="text-2xl font-bold text-foreground leading-relaxed">
              {question.question}
            </h2>
          </div>

          <div className="grid gap-3">
            {question.options.map((option, index) => {
              let variant: "primary" | "success" | "warning" = "primary";
              if (isAnswered && correctIndex !== undefined) {
                if (index === correctIndex) {
                  variant = "success";
                } else if (index === selectedAnswer && index !== correctIndex) {
                  variant = "warning";
                }
              }
              return (
                <GameButton
                  key={index}
                  variant={variant}
                  size="lg"
                  onClick={() => handleAnswerSelect(index)}
                  disabled={isAnswered}
                  className="justify-start p-6 text-left"
                >
                  <span className="mr-4 font-bold">{String.fromCharCode(65 + index)}.</span>
                  {option}
                </GameButton>
              );
            })}
          </div>
        </GameCard>

        {/* Timeout Message */}
        {isTimeout && (
          <div className="text-center mb-6">
            <div className="bg-warning/10 border border-warning text-warning px-4 py-3 rounded-md">
              <p className="font-semibold">⏰ Time's Up!</p>
              <p className="text-sm">No answer was selected. The correct answer is highlighted above.</p>
            </div>
          </div>
        )}

        {/* Next Question Button */}
        {isAnswered && !quizComplete && (
          <div className="text-center">
            {(() => {
              const hasNextQuestion = !!(window as any).__nextQuestion;
              console.log('Rendering next question button, hasNextQuestion:', hasNextQuestion, 'isAnswered:', isAnswered, 'quizComplete:', quizComplete);
              return hasNextQuestion ? (
                <GameButton variant="secondary" size="lg" onClick={nextQuestion}>
                  Next Question
                </GameButton>
              ) : (
                <span className="text-muted-foreground">Loading next question...</span>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}