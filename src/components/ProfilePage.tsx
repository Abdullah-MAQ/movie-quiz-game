import { GameCard } from "./GameCard";
import { GameButton } from "./GameButton";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Trophy, Star, Target, Calendar, TrendingUp, Award } from "lucide-react";
import { useEffect, useState } from 'react';
import { API_CONFIG } from '@/lib/config';

interface RemoteAchievement {
  id: string;
  title?: string;
  unlocked?: boolean;
  progress?: number;
  total?: number;
}

interface UserData {
  user_id: string;
  email: string;
  preferred_genre: string;
}

interface ProfilePageProps {
  userData?: UserData | null;
}

export function ProfilePage({ userData }: ProfilePageProps) {
  const [user, setUser] = useState<any>(userData || null);
  const [achievements, setAchievements] = useState<RemoteAchievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProfile = async () => {
      if (!userData?.user_id) {
        setError("No user data available");
        setLoading(false);
        return;
      }

      try {
        const res = await fetch(`${API_CONFIG.BASE_URL}/api/profile/${userData.user_id}`);
        const data = await res.json();
        
        if (!res.ok) { 
          setError(data.error || 'Failed to load profile'); 
        } else { 
          setUser(data.profile); 
          // Create some sample achievements based on user stats
          const userAchievements = generateAchievements(data.profile);
          setAchievements(userAchievements);
        }
      } catch (e: any) { 
        setError(e.message); 
      } finally { 
        setLoading(false); 
      }
    };
    
    loadProfile();
  }, [userData]);

  const generateAchievements = (profile: any): RemoteAchievement[] => {
    const achievements: RemoteAchievement[] = [
      {
        id: "first_quiz",
        title: "First Steps",
        unlocked: profile.quizzes_played >= 1,
        progress: Math.min(profile.quizzes_played, 1),
        total: 1
      },
      {
        id: "quiz_master",
        title: "Quiz Master",
        unlocked: profile.quizzes_played >= 10,
        progress: Math.min(profile.quizzes_played, 10),
        total: 10
      },
      {
        id: "streak_warrior",
        title: "Streak Warrior",
        unlocked: profile.longest_streak >= 5,
        progress: Math.min(profile.longest_streak, 5),
        total: 5
      },
      {
        id: "high_scorer",
        title: "High Scorer",
        unlocked: profile.best_score >= 1000,
        progress: Math.min(profile.best_score, 1000),
        total: 1000
      }
    ];
    
    return achievements;
  };

  if (loading) return <div className="container mx-auto px-4 py-8"><p className="text-muted-foreground">Loading profile...</p></div>;
  if (error) return <div className="container mx-auto px-4 py-8"><p className="text-destructive">{error}</p></div>;
  if (!user) return <div className="container mx-auto px-4 py-8"><p className="text-muted-foreground">No user data.</p></div>;

  const userStats = {
    name: user.display_name || user.email?.split('@')[0] || "Player",
    email: user.email || "No email",
    level: Math.max(1, Math.floor((user.total_score || 0) / 1000) + 1),
    xp: (user.total_score || 0) % 1000,
    nextLevelXp: 1000,
    totalQuizzes: user.quizzes_played || 0,
    correctAnswers: user.correct_answers || 0,
    averageScore: user.quizzes_played ? Math.round((user.total_score || 0) / user.quizzes_played) : 0,
    currentStreak: user.current_streak || 0,
    longestStreak: user.longest_streak || 0,
    favoriteCategory: user.preferred_genre || 'Not selected',
    joinDate: user.created_at || '2025-09-18'
  };

  const xpProgress = (userStats.xp / userStats.nextLevelXp) * 100;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Profile Header */}
        <GameCard variant="glow" className="p-8 mb-8">
          <div className="flex flex-col md:flex-row items-center md:items-start space-y-6 md:space-y-0 md:space-x-8">
            <div className="relative">
              <Avatar className="w-24 h-24 border-4 border-primary/30">
                <AvatarImage src="" />
                <AvatarFallback className="bg-gradient-primary text-primary-foreground text-2xl">
                  {userStats.name.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center border-2 border-background">
                <span className="text-xs font-bold text-primary-foreground">{userStats.level}</span>
              </div>
            </div>
            
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-3xl font-bold text-foreground mb-2">{userStats.name}</h1>
              <p className="text-muted-foreground mb-4">{userStats.email}</p>
              
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Level {userStats.level} Progress</span>
                  <span className="text-sm text-muted-foreground">{userStats.xp}/{userStats.nextLevelXp} XP</span>
                </div>
                <Progress value={xpProgress} className="h-3" />
              </div>
              
              <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                <Badge className="bg-success text-success-foreground">Active Player</Badge>
                <Badge className="bg-warning text-warning-foreground">Quizzer</Badge>
                {user.correct_answers >= 100 && <Badge className="bg-accent text-accent-foreground">Movie Buff</Badge>}
              </div>
            </div>

            {/* <div className="flex flex-col space-y-2">
              <GameButton variant="primary" size="sm">
                Edit Profile
              </GameButton>
              <GameButton variant="secondary" size="sm">
                Share Profile
              </GameButton>
            </div> */}
          </div>
        </GameCard>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Stats */}
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-foreground flex items-center">
              <TrendingUp className="w-6 h-6 text-primary mr-2" />
              Statistics
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <GameCard className="p-4 text-center">
                <Trophy className="w-8 h-8 text-warning mx-auto mb-2" />
                <h3 className="text-2xl font-bold text-foreground">{userStats.totalQuizzes}</h3>
                <p className="text-sm text-muted-foreground">Quizzes Played</p>
              </GameCard>
              
              {/* <GameCard className="p-4 text-center">
                <Target className="w-8 h-8 text-success mx-auto mb-2" />
                <h3 className="text-2xl font-bold text-foreground">{userStats.correctAnswers}</h3>
                <p className="text-sm text-muted-foreground">Correct Answers</p>
              </GameCard> */}
              
              <GameCard className="p-4 text-center">
                <Star className="w-8 h-8 text-accent mx-auto mb-2" />
                <h3 className="text-2xl font-bold text-foreground">{userStats.averageScore}</h3>
                <p className="text-sm text-muted-foreground">Average Score</p>
              </GameCard>
              
              <GameCard className="p-4 text-center">
                <Calendar className="w-8 h-8 text-primary mx-auto mb-2" />
                <h3 className="text-2xl font-bold text-foreground">{userStats.currentStreak}</h3>
                <p className="text-sm text-muted-foreground">Day Streak</p>
              </GameCard>
            </div>

            <GameCard className="p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Quick Stats</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Longest Streak</span>
                  <span className="text-foreground font-semibold">{userStats.longestStreak} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Favorite Category</span>
                  <span className="text-foreground font-semibold">{userStats.favoriteCategory}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Member Since</span>
                  <span className="text-foreground font-semibold">{userStats.joinDate}</span>
                </div>
              </div>
            </GameCard>
          </div>

          {/* Achievements */}
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-foreground flex items-center">
              <Award className="w-6 h-6 text-primary mr-2" />
              Achievements
            </h2>

            <div className="space-y-4">
              {achievements.length === 0 && <p className="text-muted-foreground text-sm">No achievements yet. Play some quizzes!</p>}
              {achievements.map((achievement) => (
                <GameCard key={achievement.id} variant={achievement.unlocked ? "success" : "default"} className="p-4">
                  <div className="flex items-center space-x-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${achievement.unlocked ? 'bg-gradient-success' : 'bg-muted'}`}>
                      <Star className={`w-6 h-6 ${achievement.unlocked ? 'text-success-foreground' : 'text-muted-foreground'}`} />
                    </div>
                    <div className="flex-1">
                      <h4 className={`font-semibold ${achievement.unlocked ? 'text-foreground' : 'text-muted-foreground'}`}>{achievement.title}</h4>
                      {achievement.progress !== undefined && achievement.total !== undefined && (
                        <div className="mt-2">
                          <div className="flex justify-between text-xs text-muted-foreground mb-1">
                            <span>Progress</span>
                            <span>{achievement.progress}/{achievement.total}</span>
                          </div>
                          <Progress value={(achievement.progress / achievement.total) * 100} className="h-2" />
                        </div>
                      )}
                    </div>
                    {achievement.unlocked && <Badge className="bg-success text-success-foreground">Unlocked</Badge>}
                  </div>
                </GameCard>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}