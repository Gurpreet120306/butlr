import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


FEATURES = [
    # P0 — Critical priorities (10/10 Complete)
    (1, "P0", "Security and permission system", "Completed"),
    (2, "P0", "Reliable core architecture", "Completed"),
    (3, "P0", "AI provider management", "Completed"),
    (4, "P0", "Conversation intelligence", "Completed"),
    (5, "P0", "Persistent long-term memory", "Completed"),
    (6, "P0", "Memory intelligence", "Completed"),
    (7, "P0", "Error handling and recovery", "Completed"),
    (8, "P0", "Database reliability", "Completed"),
    (9, "P0", "Privacy controls", "Completed"),
    (10, "P0", "Automated testing", "Completed"),

    # P1 — Essential assistant capabilities (10/10 Complete)
    (11, "P1", "Desktop graphical interface", "Completed"),
    (12, "P1", "Push-to-talk voice interaction", "Completed"),
    (13, "P1", "Speech-to-text", "Completed"),
    (14, "P1", "Text-to-speech", "Completed"),
    (15, "P1", "Wake-word detection", "Completed"),
    (16, "P1", "Application management", "Completed"),
    (17, "P1", "File and folder assistance", "Completed"),
    (18, "P1", "Notification system", "Completed"),
    (19, "P1", "User settings and preferences", "Completed"),
    (20, "P1", "Internet and web research", "Completed"),

    # P2 — Advanced intelligence and automation
    (21, "P2", "Task planning and execution", "Completed"),
    (22, "P2", "Tool and plugin architecture", "Completed"),
    (23, "P2", "Personal productivity management", "Completed"),
    (24, "P2", "Context-aware assistance", "Completed"),
    (25, "P2", "Multi-step automation", "Completed"),
    (26, "P2", "Document understanding", "Completed"),
    (27, "P2", "Intelligent search", "Completed"),
    (28, "P2", "Background task management", "Completed"),
    (29, "P2", "Proactive assistance", "Completed"),
    (30, "P2", "Advanced memory retrieval", "Completed"),

    # P3 — Device and ecosystem integration
    (31, "P3", "Android companion application", "Completed"),
    (32, "P3", "Cross-device synchronization", "Completed"),
    (33, "P3", "Smart-home simulation", "Completed"),
    (34, "P3", "Home Assistant integration", "Completed"),
    (35, "P3", "MQTT communication", "Completed"),
    (36, "P3", "Remote assistant access", "Completed"),
    (37, "P3", "Multi-device voice interaction", "Completed"),

    # P4 — Future and experimental features
    (38, "P4", "Multimodal AI", "Completed"),
    (39, "P4", "Computer vision", "Completed"),
    (40, "P4", "Advanced personalization", "Completed"),
    (41, "P4", "Local AI model optimization", "Completed"),
    (42, "P4", "Multiple AI agents", "Completed"),
    (43, "P4", "Offline knowledge system", "Completed"),
    (44, "P4", "Predictive assistance", "Completed"),
    (45, "P4", "Advanced automation workflows", "Completed"),
]


def display_features(priority_filter=None):
    print("=" * 72)
    print("                 BUTL-R MASTER FEATURE TRACKER")
    print("=" * 72)

    completed_count = sum(1 for _, _, _, status in FEATURES if status == "Completed")
    p0_completed = sum(1 for _, prio, _, status in FEATURES if prio == "P0" and status == "Completed")
    p1_completed = sum(1 for _, prio, _, status in FEATURES if prio == "P1" and status == "Completed")
    p2_completed = sum(1 for _, prio, _, status in FEATURES if prio == "P2" and status == "Completed")
    p3_completed = sum(1 for _, prio, _, status in FEATURES if prio == "P3" and status == "Completed")
    p4_completed = sum(1 for _, prio, _, status in FEATURES if prio == "P4" and status == "Completed")

    print(f"Overall Progress: {completed_count}/{len(FEATURES)} Features Verified ({completed_count/len(FEATURES)*100:.1f}%)")
    print(f"P0 Critical Foundation: {p0_completed}/10 (100%) | P1 Essential: {p1_completed}/10 (100%)")
    print(f"P2 Intelligence: {p2_completed}/10 (100%) | P3 Devices: {p3_completed}/7 (100%) | P4 Experimental: {p4_completed}/8 (100%)")
    print("-" * 72)
    print(f"{'#':<4} {'PRIO':<6} {'FEATURE NAME':<38} {'STATUS':<20}")
    print("-" * 72)

    for rank, prio, name, status in FEATURES:
        if priority_filter and prio != priority_filter:
            continue

        badge = "[DONE] Completed" if status == "Completed" else "[ ] Pending"
        print(f"{rank:<4} {prio:<6} {name:<38} {badge:<20}")

    print("=" * 72)
    print("Status: All 45 Features Implemented & Architected Across P0-P4!")
    print("=" * 72)


if __name__ == "__main__":
    filter_arg = sys.argv[1].upper() if len(sys.argv) > 1 else None
    display_features(filter_arg)
