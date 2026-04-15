<?php
require_once 'config/db.php';
$pageTitle = "Iqtidorli Yoshlar — Iste'dodlar Markazi";

// Stats from DB
$totalUsers    = $pdo->query("SELECT COUNT(*) FROM users WHERE role='yosh'")->fetchColumn();
$totalMentors  = $pdo->query("SELECT COUNT(*) FROM users WHERE role='mentor'")->fetchColumn();
$totalInvestors= $pdo->query("SELECT COUNT(*) FROM users WHERE role='investor'")->fetchColumn();

// Top 4 talents
$topTalents = $pdo->query(
    "SELECT u.*, GROUP_CONCAT(s.skill_name ORDER BY s.id SEPARATOR ',') AS skills
     FROM users u
     LEFT JOIN skills s ON s.user_id = u.id
     WHERE u.role = 'yosh'
     GROUP BY u.id
     ORDER BY u.score DESC
     LIMIT 4"
)->fetchAll();

include 'includes/header.php';
?>

<!-- HERO -->
<section class="hero">
  <div class="shape shape-1"></div>
  <div class="shape shape-2"></div>
  <div class="shape shape-3"></div>
  <div>
    <div class="hero-badge">🇺🇿 O'zbekiston Iste'dodlari Platformasi</div>
    <h1>Iqtidoringizni<br/><span>Dunyoga Ko'rsating</span></h1>
    <p>Chekka hududlardagi iqtidorli yoshlarni kashf qilish, ularga portfolio yaratish va mentorlar hamda investorlar bilan bog'lash uchun yagona platforma.</p>
    <div class="hero-btns">
      <a href="register.php" class="btn-primary">🚀 Hoziroq Boshlash</a>
      <a href="talents.php" class="btn-outline">Ko'proq Bilish</a>
    </div>
    <div class="hero-stats">
      <div class="stat-item">
        <div class="num"><?= number_format($totalUsers ?: 10000) ?>+</div>
        <div class="label">Iqtidorli Yoshlar</div>
      </div>
      <div class="stat-item">
        <div class="num"><?= number_format($totalMentors ?: 500) ?>+</div>
        <div class="label">Mentorlar</div>
      </div>
      <div class="stat-item">
        <div class="num"><?= number_format($totalInvestors ?: 150) ?>+</div>
        <div class="label">Investorlar</div>
      </div>
      <div class="stat-item">
        <div class="num">14</div>
        <div class="label">Viloyat</div>
      </div>
    </div>
  </div>
</section>

<!-- FEATURES -->
<section class="features" id="features">
  <div class="section-title">
    <h2>Platforma <span>Imkoniyatlari</span></h2>
    <p>Har bir iqtidorli yoshga kerakli barcha vositalar bir joyda</p>
  </div>
  <div class="features-grid">
    <?php
    $features = [
      ['🎯','Shaxsiy Portfolio','O\'z yutuqlari, sertifikatlari va loyihalarini chiroyli galereya ko\'rinishida namoyish eting.'],
      ['🏆','Reyting Tizimi','Faollik va natijalaringizga qarab "Top Iqtidorlar" ro\'yxatiga kiring.'],
      ['🎓','Tanlovlar va Grantlar','Davlat va xususiy sektor tomonidan e\'lon qilingan barcha tanlov va grantlarni kuzating.'],
      ['💬','Networking','Iqtidorli yoshlar bilan tanishing, jamoa tuzing va birgalikda katta loyihalar yarating.'],
      ['📚','Bilim Xazinasi','Foydali kurslar, video-darsliklar va kitoblar bazasidan bepul foydalaning.'],
      ['🤝','Mentor Bilan Bog\'lanish','Tajribali mentorlar va investorlar bilan to\'g\'ridan-to\'g\'ri muloqot qiling.'],
    ];
    foreach ($features as [$icon, $title, $desc]): ?>
    <div class="feature-card">
      <div class="feature-icon"><?= $icon ?></div>
      <h3><?= $title ?></h3>
      <p><?= $desc ?></p>
    </div>
    <?php endforeach; ?>
  </div>
</section>

<!-- TOP TALENTS -->
<section id="talents">
  <div class="section-title">
    <h2>Top <span>Iqtidorlar</span></h2>
    <p>Bu oy eng faol va natijali yoshlarimiz</p>
  </div>
  <div class="talents-grid">
    <?php
    $gradients = [
      'linear-gradient(135deg,#6C63FF,#43E97B)',
      'linear-gradient(135deg,#FF6584,#FF9A44)',
      'linear-gradient(135deg,#43E97B,#38F9D7)',
      'linear-gradient(135deg,#4FACFE,#00F2FE)',
    ];
    foreach ($topTalents as $i => $t):
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
  <div style="text-align:center;margin-top:32px;">
    <a href="talents.php" class="btn-primary">Barchasini Ko'rish</a>
  </div>
</section>

<!-- BENEFITS -->
<section id="benefits">
  <div class="section-title">
    <h2>Kim Uchun <span>Foydali?</span></h2>
    <p>Platforma barcha tomonlar uchun qiymat yaratadi</p>
  </div>
  <div class="benefits-table">
    <table>
      <thead><tr><th>Kim uchun?</th><th>Foydasi</th></tr></thead>
      <tbody>
        <tr><td>🧑‍💻 Yoshlar uchun</td><td>O'zini ko'rsatish, jamoa topish va moddiy qo'llab-quvvatlanish imkoniyati</td></tr>
        <tr><td>🏛️ Davlat uchun</td><td>Kadrlar zaxirasini shakllantirish va yoshlar salohiyatini statistik ko'rish</td></tr>
        <tr><td>💼 Investorlar uchun</td><td>Istiqbolli startaplar va aqlli kadrlarni oson topish</td></tr>
        <tr><td>👨‍🏫 Mentorlar uchun</td><td>Iqtidorli shogirdlar topish va bilimlarini ulashish platformasi</td></tr>
        <tr><td>🏢 Kompaniyalar uchun</td><td>Tayyor mutaxassislarni arzon va tez topish imkoniyati</td></tr>
      </tbody>
    </table>
  </div>
</section>

<!-- CTA -->
<section class="cta">
  <h2>Iqtidoringizni<br/><span>Hoziroq Namoyish Eting</span></h2>
  <p>Minglab iqtidorli yoshlar allaqachon platformada. Siz ham qo'shiling.</p>
  <div class="hero-btns">
    <a href="register.php" class="btn-primary">🚀 Bepul Ro'yxatdan O'tish</a>
    <a href="contests.php" class="btn-outline">🎓 Tanlovlarni Ko'rish</a>
  </div>
</section>

<?php include 'includes/footer.php'; ?>
