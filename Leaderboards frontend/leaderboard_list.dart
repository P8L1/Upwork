// lib/leaderboards/leaderboard_list.dart
import 'package:flutter/material.dart';
import 'league_model.dart';

class LeaderboardList extends StatelessWidget {
  final List<LeaderboardEntry> entries;

  const LeaderboardList({Key? key, required this.entries}) : super(key: key);

  Widget _buildRankIcon(int rank) {
    // rank is 0-based index; actual rank is rank+1
    switch (rank) {
      case 0:
        return Image.asset('images/1st.png', width: 20, height: 20);
      case 1:
        return Image.asset('images/2nd.png', width: 20, height: 20);
      case 2:
        return Image.asset('images/3rd.png', width: 20, height: 20);
      default:
        // For ranks beyond 3rd, just show text
        return Text(
          (rank + 1).toString(),
          style: TextStyle(
            color: _getColorForRank(rank, entries.length),
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        );
    }
  }

  Color _getColorForRank(int rank, int total) {
    final promotedCount = 7;
    final demotedCount = 7;

    if (rank < promotedCount) {
      return Colors.blue;
    } else if (rank >= total - demotedCount) {
      return Colors.red;
    } else {
      return Colors.green;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: entries.length,
      itemBuilder: (context, index) {
        final entry = entries[index];

        return Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            children: [
              _buildRankIcon(index),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  entry.username,
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                ),
              ),
              Text(
                "${entry.expEarned} XP",
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ],
          ),
        );
      },
    );
  }
}
