import { useState, useEffect } from "react";
import { GameCard } from "./GameCard";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Trophy, Medal, Award, Star, TrendingUp } from "lucide-react";
import { API_CONFIG } from '@/lib/config';

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name: string;
  email: string;
  preferred_genre: string;
  total_score: number;
  quizzes_played: number;
  current_streak: number;
  best_score: number;
  badge?: "champion" | "rising" | "veteran";
}

interface UserData {
  user_id: string;
  email: string;
  preferred_genre: string;
}

interface LeaderboardPageProps {
  userData?: UserData | null;
}

export function LeaderboardPage({ userData }: LeaderboardPageProps) {
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPlayers, setTotalPlayers] = useState(0);
  const [totalQuizzes, setTotalQuizzes] = useState(0);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/leaderboard`);
        const data = await response.json();
        
        if (response.ok) {
          const entries = data.leaderboard.map((entry: any) => ({
            ...entry,
            name: entry.name,
            score: entry.total_score,
            quizzesPlayed: entry.quizzes_played,
            streak: entry.current_streak,
            badge: getBadgeForUser(entry)
          }));
          
          setLeaderboardData(entries);
          setTotalPlayers(entries.length);
          setTotalQuizzes(entries.reduce((sum: number, entry: any) => sum + entry.quizzes_played, 0));
        } else {
          setError(data.error || "Failed to load leaderboard");
        }
      } catch (err) {
        setError("Network error. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, []);

  const getBadgeForUser = (entry: any): "champion" | "rising" | "veteran" | undefined => {
    if (entry.rank === 1) return "champion";
    if (entry.current_streak >= 5) return "rising";
    if (entry.quizzes_played >= 10) return "veteran";
    return undefined;
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="w-6 h-6 text-warning" />;
      case 2:
        return <Medal className="w-6 h-6 text-muted-foreground" />;
      case 3:
        return <Award className="w-6 h-6 text-accent" />;
      default:
        return <span className="w-6 h-6 flex items-center justify-center text-muted-foreground font-bold">#{rank}</span>;
    }
  };

  const getBadgeColor = (badge?: string) => {
    switch (badge) {
      case "champion":
        return "bg-warning text-warning-foreground";
      case "rising":
        return "bg-success text-success-foreground";
      case "veteran":
        return "bg-primary text-primary-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-4">
            Global Leaderboard
          </h1>
          <p className="text-muted-foreground text-lg">
            Compete with movie enthusiasts worldwide
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <GameCard className="p-6 text-center">
            <Trophy className="w-8 h-8 text-warning mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-foreground">{totalPlayers}</h3>
            <p className="text-muted-foreground">Total Players</p>
          </GameCard>
          <GameCard className="p-6 text-center">
            <Star className="w-8 h-8 text-accent mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-foreground">{totalQuizzes}</h3>
            <p className="text-muted-foreground">Quizzes Completed</p>
          </GameCard>
          <GameCard className="p-6 text-center">
            <TrendingUp className="w-8 h-8 text-success mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-foreground">
              {totalQuizzes > 0 && totalPlayers > 0 ? Math.round((totalQuizzes / totalPlayers) * 10) / 10 : 0}
            </h3>
            <p className="text-muted-foreground">Avg Quizzes/Player</p>
          </GameCard>
        </div>

        {/* Leaderboard */}
        <GameCard variant="glow" className="overflow-hidden">
          <div className="p-6">
            <h2 className="text-2xl font-bold text-foreground mb-6 flex items-center">
              <Trophy className="w-6 h-6 text-warning mr-2" />
              Top Players
            </h2>
            
            {loading && (
              <div className="text-center py-8">
                <p className="text-muted-foreground">Loading leaderboard...</p>
              </div>
            )}
            
            {error && (
              <div className="text-center py-8">
                <p className="text-destructive">{error}</p>
              </div>
            )}
            
            {!loading && !error && leaderboardData.length === 0 && (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No players yet. Be the first to play!</p>
              </div>
            )}
            
            <div className="space-y-3">
              {leaderboardData.map((entry) => (
                <div
                  key={entry.user_id}
                  className={`flex items-center justify-between p-4 rounded-lg transition-all duration-300 ${
                    userData?.user_id === entry.user_id
                      ? "bg-primary/10 border-2 border-primary/30 shadow-glow" 
                      : "bg-muted/30 hover:bg-muted/50"
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {getRankIcon(entry.rank)}
                    </div>
                    
                    <Avatar className="w-10 h-10">
                      <AvatarFallback className="bg-gradient-primary text-primary-foreground">
                        {entry.name.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-foreground">
                          {entry.name} {userData?.user_id === entry.user_id && "(You)"}
                        </h3>
                        {entry.badge && (
                          <Badge className={getBadgeColor(entry.badge)}>
                            {entry.badge}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {entry.quizzes_played} quizzes • {entry.current_streak} streak • {entry.preferred_genre}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-2xl font-bold text-foreground">
                      {entry.total_score.toLocaleString()}
                    </p>
                    <p className="text-sm text-muted-foreground">points</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GameCard>
      </div>
    </div>
  );
}