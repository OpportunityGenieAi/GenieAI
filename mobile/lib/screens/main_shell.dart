import 'package:flutter/material.dart';

import 'advisor/advisor_screen.dart';
import 'home/home_screen.dart';
import 'match/match_screen.dart';
import 'profile/profile_screen.dart';
import 'tracker/tracker_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});
  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  static const _screens = [
    HomeScreen(),
    MatchScreen(),
    TrackerScreen(),
    AdvisorScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.bolt_outlined), activeIcon: Icon(Icons.bolt), label: 'Match'),
          BottomNavigationBarItem(icon: Icon(Icons.list_alt_outlined), activeIcon: Icon(Icons.list_alt), label: 'Tracker'),
          BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), activeIcon: Icon(Icons.chat_bubble), label: 'Advisor'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
