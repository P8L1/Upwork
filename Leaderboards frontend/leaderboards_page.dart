// leaderboards_page.dart

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'leaderboard_service.dart';
import 'league_icon.dart';
import 'league_model.dart';
import 'leaderboard_list.dart';
import 'countdown_timer.dart';
import 'locked_out_screen.dart';
import 'league_change_screen.dart';

class LeaderboardsPage extends StatefulWidget {
  final String token;
  const LeaderboardsPage({Key? key, required this.token}) : super(key: key);

  @override
  _LeaderboardsPageState createState() => _LeaderboardsPageState();
}

class _LeaderboardsPageState extends State<LeaderboardsPage> {
  bool isLoading = true;
  bool lockedOut = false;
  String currentLeague = "";
  double countdownSeconds = 0;

  // For rank-outcome:
  int finishedRank = 0;
  String oldLeague = "";
  String newLeague = "";

  List<League> leagues = [];
  List<LeaderboardEntry> leaderboard = [];

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    debugPrint('[LeaderboardsPage] _fetchData() called.');

    // Indicate loading has started
    setState(() {
      isLoading = true;
      debugPrint('[LeaderboardsPage] setState: isLoading set to true.');
    });

    final stopwatch = Stopwatch()..start();
    debugPrint('[LeaderboardsPage] Stopwatch started.');

    try {
      debugPrint('[LeaderboardsPage] Initializing LeaderboardService with token: ${widget.token}');
      final service = LeaderboardService(token: widget.token);

      debugPrint('[LeaderboardsPage] Calling fetchCurrentLeagueData().');
      final data = await service.fetchCurrentLeagueData();
      debugPrint('[LeaderboardsPage] Data fetched: $data');

      // --- STEP 1: Parse incoming data ---

      final bool apiLockedOut = data['locked_out'] ?? false;
      debugPrint('[LeaderboardsPage] apiLockedOut = $apiLockedOut');

      final outcome = data['outcome'] ?? {};
      debugPrint('[LeaderboardsPage] outcome data: $outcome');

      finishedRank = outcome['finished_rank'] ?? 0;
      oldLeague = outcome['old_league'] ?? "";
      newLeague = outcome['new_league'] ?? "";

      currentLeague = data['currentLeague'] ?? "";
      countdownSeconds = (data['countdown_seconds'] ?? 0).toDouble();

      // Process leagues
      final leaguesData = (data['leagues'] ?? []) as List<dynamic>;
      leagues = leaguesData.map((l) {
        return League(
          name: l['name'],
          icon: l['icon'],
          order: l['order'],
        );
      }).toList();

      // Process leaderboard entries
      final leaderboardData = (data['leaderboard'] ?? []) as List<dynamic>;
      leaderboard = leaderboardData.map((entry) {
        final user = entry['user'];
        if (user == null) {
          return LeaderboardEntry(
            username: 'Unknown',
            email: 'Unknown',
            expEarned: entry['exp_earned'] ?? 0,
          );
        }
        return LeaderboardEntry(
          username: user['username'] ?? 'Unknown',
          email: user['email'] ?? 'Unknown',
          expEarned: entry['exp_earned'] ?? 0,
        );
      }).toList();

      // --- STEP 2: Decide if user is locked out ---

      // If the API says locked_out is true OR currentLeague is empty,
      // we consider them locked out. (You can refine this logic as needed.)
      lockedOut = apiLockedOut || currentLeague.isEmpty;
      debugPrint('[LeaderboardsPage] lockedOut is now: $lockedOut');
      debugPrint('[LeaderboardsPage] currentLeague is: "$currentLeague"');

      // Indicate data has finished loading
      setState(() {
        isLoading = false;
        debugPrint('[LeaderboardsPage] setState: isLoading set to false.');
      });

      // Stop the stopwatch
      stopwatch.stop();
      debugPrint('[LeaderboardsPage] Data fetching and processing completed in ${stopwatch.elapsedMilliseconds} ms.');

      // Immediately check if we must navigate the user to locked screen, etc.
      _handlePotentialScreens();

    } catch (e, stackTrace) {
      stopwatch.stop();
      debugPrint('[LeaderboardsPage] Error fetching data: $e');
      debugPrint('[LeaderboardsPage] StackTrace: $stackTrace');
      debugPrint('[LeaderboardsPage] Data fetching failed after ${stopwatch.elapsedMilliseconds} ms.');

      setState(() {
        isLoading = false;
        debugPrint('[LeaderboardsPage] setState: isLoading set to false due to error.');
      });
    } finally {
      debugPrint('[LeaderboardsPage] _fetchData() execution finished.');
    }
  }

  /// If the user is locked out, navigate to the locked out screen.
  /// If outcome indicates a promotion/demotion, show that screen, etc.
  void _handlePotentialScreens() {
    if (lockedOut) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LockedOutScreen()),
      );
      return;
    }

    // If the user’s oldLeague != newLeague, we can show the promotion/demotion screen.
    if (oldLeague.isNotEmpty && oldLeague != newLeague) {
      final wasPromoted = _checkPromotion(oldLeague, newLeague);
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => LeagueChangeScreen(
            finishedRank: finishedRank,
            wasPromoted: wasPromoted,
            newLeagueName: newLeague,
          ),
        ),
      );
      return;
    }
  }

  bool _checkPromotion(String oldL, String newL) {
    // If leagues is empty, or we can't find old/new, default to no promotion
    if (leagues.isEmpty) return false;

    final oldIndex = leagues.firstWhere(
      (l) => l.name == oldL,
      orElse: () => leagues.first,
    ).order;

    final newIndex = leagues.firstWhere(
      (l) => l.name == newL,
      orElse: () => leagues.last,
    ).order;

    return newIndex > oldIndex;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        automaticallyImplyLeading: false,
        title: const Text(
          "Leaderboards",
          style: TextStyle(color: Colors.white),
        ),
        leadingWidth: 56,
        leading: GestureDetector(
          onTap: () => Navigator.of(context).pop(),
          child: Container(
            alignment: Alignment.center,
            child: Image.asset(
              'images/back_icon.png',
              width: 22,
              height: 22,
              fit: BoxFit.contain,
            ),
          ),
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.white))
          : Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Countdown
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: CountdownTimer(countdownSeconds: countdownSeconds),
                ),

                // League icons row
                LeagueIconRow(
                  leagues: leagues,
                  // If leagues is empty, we fallback to 0
                  currentLeagueOrder: leagues.isEmpty
                      ? 0
                      : leagues
                          .firstWhere(
                            (l) => l.name == currentLeague,
                            orElse: () => leagues.first,
                          )
                          .order,
                ),

                // Leaderboard
                Expanded(
                  child: LeaderboardList(entries: leaderboard),
                ),
              ],
            ),
    );
  }
}
