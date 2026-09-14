import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart' show LaunchMode;
import 'package:url_launcher/url_launcher_string.dart';

import '../models/scholarship.dart';
import '../theme/app_theme.dart';

class ScholarshipCard extends StatelessWidget {
  final Scholarship scholarship;
  final bool isBookmarked;
  final bool showMatch;
  final VoidCallback? onToggleBookmark;

  const ScholarshipCard({
    super.key,
    required this.scholarship,
    this.isBookmarked = false,
    this.showMatch = false,
    this.onToggleBookmark,
  });

  Color _matchColor(String? tier) {
    switch (tier) {
      case 'green':
        return AppColors.green;
      case 'yellow':
        return AppColors.amber;
      case 'red':
        return AppColors.red;
      default:
        return AppColors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(scholarship.name,
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 2),
                    Text(scholarship.provider,
                        style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (showMatch && scholarship.matchScore != null)
                    Text('${scholarship.matchScore}%',
                        style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w800,
                            color: _matchColor(scholarship.matchTier))),
                  const SizedBox(height: 8),
                  InkWell(
                    onTap: onToggleBookmark,
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      width: 30,
                      height: 30,
                      decoration: BoxDecoration(
                        color: isBookmarked ? AppColors.blue : Colors.white,
                        shape: BoxShape.circle,
                        border: Border.all(color: isBookmarked ? AppColors.blue : AppColors.line),
                      ),
                      child: Icon(
                        isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                        size: 15,
                        color: isBookmarked ? Colors.white : AppColors.inkSoft,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(scholarship.blurb, style: Theme.of(context).textTheme.bodySmall?.copyWith(height: 1.5)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 14,
            runSpacing: 6,
            children: [
              _metaItem(Icons.location_on_outlined, scholarship.country),
              _metaItem(Icons.attach_money, scholarship.funding),
              _metaItem(Icons.access_time, scholarship.deadlineWindow),
            ],
          ),
          if (scholarship.tags.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: scholarship.tags
                  .map((t) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 4),
                        decoration: BoxDecoration(color: AppColors.blueTint, borderRadius: BorderRadius.circular(20)),
                        child: Text(t, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: AppColors.blue)),
                      ))
                  .toList(),
            ),
          ],
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => launchUrlString(scholarship.officialLink, mode: LaunchMode.externalApplication),
              child: const Text('Apply on official site'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _metaItem(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: AppColors.inkSoft),
        const SizedBox(width: 5),
        Text(label, style: const TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
      ],
    );
  }
}
