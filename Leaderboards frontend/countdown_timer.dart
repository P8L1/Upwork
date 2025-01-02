// lib/leaderboards/countdown_timer.dart
import 'package:flutter/material.dart';
import 'dart:async';

class CountdownTimer extends StatefulWidget {
  final double countdownSeconds;

  const CountdownTimer({Key? key, required this.countdownSeconds})
      : super(key: key);

  @override
  _CountdownTimerState createState() => _CountdownTimerState();
}

class _CountdownTimerState extends State<CountdownTimer> {
  late int remainingSeconds;
  Timer? timer;

  @override
/*************  ✨ Codeium Command ⭐  *************/
  /// Initializes the countdown timer by setting its initial value to
  /// [widget.countdownSeconds] and starting a periodic timer that
  /// decrements the value every second until it reaches 0.
/******  87b8a6fb-1dd9-4c74-8763-022f2e2a20ca  *******/  void initState() {
    super.initState();
    remainingSeconds = widget.countdownSeconds.toInt();
    timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (remainingSeconds <= 0) {
        timer.cancel();
      } else {
        setState(() {
          remainingSeconds -= 1;
        });
      }
    });
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  String formatTime(int seconds) {
    final days = seconds ~/ 86400;
    final hours = (seconds % 86400) ~/ 3600;
    final minutes = (seconds % 3600) ~/ 60;
    final secs = seconds % 60;

    if (days > 0) {
      return "${days}d ${hours}h ${minutes}m ${secs}s";
    } else if (hours > 0) {
      return "${hours}h ${minutes}m ${secs}s";
    } else if (minutes > 0) {
      return "${minutes}m ${secs}s";
    } else {
      return "${secs}s";
    }
  }

  @override
  Widget build(BuildContext context) {
    return Text(
      "Resets in: ${formatTime(remainingSeconds)}",
      style: const TextStyle(color: Colors.white, fontSize: 16),
    );
  }
}
