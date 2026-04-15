<?php
require_once 'config/db.php';
$pageTitle = 'Top Iqtidorlar';

$region = trim($_GET['region'] ?? '');
$search = trim($_GET['q'] ?? '');

$where = ["u.role = 'yosh'"];
$params = [];

if ($region) {
    $where[] = "u.region = ?";
    $params[] = $region;
}
if ($search) {
    $where[] = "(u.full_name LIKE ? OR u.bio LIKE ?)";
    $params[] = "%$search%";
    $params[] = "%$search%";
}

$sql = "SELECT u.*, GROUP_CONCAT(s.skill_name ORDER BY s.id SEPARATOR ',') AS skills
        FROM users u
        LEFT JOIN skills s ON s.user_id = u.id
        WHERE " . implode(' AND ', $where) . "
        GROUP BY u.id
        ORDER BY u.score DESC";

$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$talents = $stmt->fetchAll();

$regions = $pdo->query("SELECT DISTINCT region FROM users WHERE region IS NOT NULL AND region != '' ORDER BY region")->fetchAll(PDO::FETCH_COLUMN);

$gradients = [
    'linear-gradient(135deg,#6C63FF,#43E97B)',
    'linear-gradient(135deg,#FF6584,#FF9A44)',
    'linear-gradient(135deg,#43E97B,#38F9D7)',
    'linear-gradient(135deg,#4FACFE,#00F2FE)',
    'linear-gradient(135deg,#f093fb,#f5576c)',
    'linear-gradient(135deg,#4facfe,#00f2fe)',
];

include 'includes/header.php';
?>

<section style="padding-top:120px;">
  <div class="section-title">
    <h2>Top <span>Iqtidorlar</span></h2>
    <p>Platformadagi eng faol va natijali yoshlar</p>
  </div>

  <!-- Filter -->
  <form method="GET" class="filter-form">
    <input type="text" name="q" placeholder="🔍 Ism yoki kasb bo'yicha qidirish..."
           value="<?= htmlspecialchars($search) ?>"/>
    <select name="region">
      <option value="">Barcha viloyatlar</option>
      <?php foreach ($regions as $r): ?>
        <option value="<?= htmlspecialchars($r) ?>" <?= $region === $r ? 'selected' : '' ?>>
          <?= htmlspecialchars($r) ?>
        </option>
      <?php endforeach; ?>
    </select>
    <button type="submit" class="btn-primary">Qidirish</button>
    <?php if ($region || $search): ?>
      <a href="talents.php" class="btn-outline">Tozalash</a>
    <?php endif; ?>
  </form>

  <?php if ($talents): ?>
    <div class="talents-grid" style="max-width:1200px;margin:0 auto;">
      <?php foreach ($talents as $i => $t):
        $initial = mb_strtoupper(mb_substr($t['full_name'], 0, 1));
        $grad    = $gradients[$i % count($gradients)];
        $tags    = $t['skills'] ? explode(',', $t['skills']) : [];
      ?>
        <div class="talent-card">
          <div class="talent-avatar" style="background:<?= $grad ?>;"><?= $initial ?></div>
          <h4><?= htmlspecialchars($t['full_name']) ?></h4>
          <div class="role"><?= htmlspecialchars($t['bio'] ?? 'Iqtidorli Yosh') ?></div>
          <div class="region">📍 <?= htmlspecialchars($t['region'] ?? '') ?></div>
          <div class="talent-score">⭐ <?= $t['score'] ?> ball</div>
          <div class="talent-tags">
            <?php foreach ($tags as $tag): ?>
              <span class="tag"><?= htmlspecialchars(trim($tag)) ?></span>
            <?php endforeach; ?>
          </div>
        </div>
      <?php endforeach; ?>
    </div>
  <?php else: ?>
    <p style="text-align:center;color:var(--muted);padding:40px;">Hech narsa topilmadi.</p>
  <?php endif; ?>
</section>

<?php include 'includes/footer.php'; ?>
