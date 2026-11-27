"""GTA VI leaked Tex2 console settings, cost weights, and quick presets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BadgeType = Literal["CPU", "GPU", "RT", "VRAM", "RAM"]


@dataclass(frozen=True, slots=True)
class ResolutionProfile:
    """Output display resolution scaling factor and framebuffer VRAM delta."""

    id: str
    label: str
    base_res_factor: float
    vram_delta_gb: float


@dataclass(frozen=True, slots=True)
class UpscalerProfile:
    """Internal render resolution multiplier for native or spatial/temporal upscalers."""

    id: str
    generic_label: str
    render_multiplier: float
    description_en: str
    description_fa: str

    def display_label(self, brand: str) -> str:
        """Return vendor-specific pill label (DLSS / FSR / XeSS)."""
        if self.id == "native":
            return "Native"
        if self.id == "native_aa":
            aa_name = "DLAA" if brand == "DLSS" else f"{brand} AA"
            return f"Native AA ({aa_name})"
        return f"{brand} {self.generic_label}"


@dataclass(frozen=True, slots=True)
class FrameGenProfile:
    """Frame generation mode multiplier and compatibility constraint."""

    id: str
    label: str
    fps_multiplier: float
    base_overhead: float
    requires_fg: bool
    requires_mfg: bool


@dataclass(frozen=True, slots=True)
class SettingOption:
    """Single quality tier for a graphics setting with deltas relative to PS5 baseline."""

    label: str
    raster_cost: float = 0.0
    rt_cost: float = 0.0
    cpu_cost: float = 0.0
    vram_mb: float = 0.0
    ram_mb: float = 0.0


@dataclass(frozen=True, slots=True)
class SettingDefinition:
    """Metadata and options for a categorized GTA VI graphics setting."""

    id: str
    name: str
    category: str
    badges: tuple[BadgeType, ...]
    options: tuple[SettingOption, ...]
    default_option: str
    tex2_subsettings: str
    tooltip_en: str
    tooltip_fa: str

    def option_labels(self) -> list[str]:
        return [opt.label for opt in self.options]

    def get_option(self, label: str) -> SettingOption:
        for opt in self.options:
            if opt.label == label:
                return opt
        return self.get_option_default()

    def get_option_default(self) -> SettingOption:
        for opt in self.options:
            if opt.label == self.default_option:
                return opt
        return self.options[0]


@dataclass(frozen=True, slots=True)
class SettingsPreset:
    """Named graphics preset with optional display resolution/upscaler overrides."""

    id: str
    label: str
    values: dict[str, str]
    resolution_id: str | None = None
    upscaler_id: str | None = None
    description_en: str = ""
    description_fa: str = ""


SETTING_CATEGORIES: tuple[str, ...] = (
    "Lighting & RT",
    "Textures & World",
    "Water",
    "Volumetrics & Particles",
    "Hair",
    "Population / AI / Physics",
)

RESOLUTIONS: tuple[ResolutionProfile, ...] = (
    ResolutionProfile("720p", "720p", 0.34, -0.6),
    ResolutionProfile("900p", "900p", 0.46, -0.3),
    ResolutionProfile("1080p", "1080p", 0.62, 0.0),
    ResolutionProfile("1440p", "1440p", 1.00, 0.9),
    ResolutionProfile("4k", "4K", 1.92, 2.1),
)

UPSCALERS: tuple[UpscalerProfile, ...] = (
    UpscalerProfile(
        id="native",
        generic_label="Native",
        render_multiplier=1.00,
        description_en="Full native pixel rendering without spatial upscaling.",
        description_fa="رندر کامل رزولوشن بومی بدون ارتقای تصویر.",
    ),
    UpscalerProfile(
        id="native_aa",
        generic_label="Native AA",
        render_multiplier=1.04,
        description_en="Native resolution with AI/temporal anti-aliasing (~4% shader cost).",
        description_fa="رزولوشن بومی همراه با آنتی‌آلیاسینگ هوش مصنوعی (حدود ۴٪ بار اضافه).",
    ),
    UpscalerProfile(
        id="quality",
        generic_label="Quality",
        render_multiplier=0.55,
        description_en="~67% internal resolution scale; high clarity + strong FPS gain.",
        description_fa="مقیاس داخلی حدود ۶۷٪؛ وضوح عالی با افزایش چشمگیر فریم‌ریت.",
    ),
    UpscalerProfile(
        id="balanced",
        generic_label="Balanced",
        render_multiplier=0.45,
        description_en="~58% internal resolution scale; great middle ground at 1440p/4K.",
        description_fa="مقیاس داخلی حدود ۵۸٪؛ تعادل مناسب برای 1440p و 4K.",
    ),
    UpscalerProfile(
        id="performance",
        generic_label="Performance",
        render_multiplier=0.37,
        description_en="~50% internal resolution scale; maximizes GPU headroom.",
        description_fa="مقیاس داخلی ۵۰٪؛ بیشترین افزایش فریم برای کارت‌های ضعیف‌تر یا 4K.",
    ),
)

FRAME_GEN_MODES: tuple[FrameGenProfile, ...] = (
    FrameGenProfile("off", "Off", 1.00, 0.00, requires_fg=False, requires_mfg=False),
    FrameGenProfile("2x", "2x FG", 1.72, 0.08, requires_fg=True, requires_mfg=False),
    FrameGenProfile("3x", "MFG 3x", 2.40, 0.09, requires_fg=True, requires_mfg=True),
    FrameGenProfile("4x", "MFG 4x", 3.00, 0.10, requires_fg=True, requires_mfg=True),
)

SETTINGS: tuple[SettingDefinition, ...] = (
    SettingDefinition(
        id="rtgi",
        name="Global Illumination (RTGI)",
        category="Lighting & RT",
        badges=("RT", "VRAM"),
        options=(
            SettingOption("Medium", rt_cost=0.00, vram_mb=0.0),
            SettingOption("High", rt_cost=0.28, vram_mb=450.0),
            SettingOption("Ultra", rt_cost=0.55, vram_mb=800.0),
        ),
        default_option="Medium",
        tex2_subsettings="Diffuse GI, Probe Resolution, Bounce Count, GI Radiance Cache",
        tooltip_en=(
            "Hardware ray-traced diffuse global illumination (always active from Medium upward). "
            "High/Ultra dramatically increases RT core load and GI probe VRAM footprint."
        ),
        tooltip_fa=(
            "نورپردازی سراسری ردیابی پرتو (RTGI) که از سطح Medium همیشه فعال است. "
            "افزایش آن فشار سنگینی به هسته‌های RT و حافظه VRAM وارد می‌کند."
        ),
    ),
    SettingDefinition(
        id="rt_shadows",
        name="Ray-Traced Shadows (Dir + Local + LOD)",
        category="Lighting & RT",
        badges=("RT", "CPU", "VRAM"),
        options=(
            SettingOption("Off / None", rt_cost=0.00, cpu_cost=0.00, vram_mb=0.0),
            SettingOption("Medium", rt_cost=0.22, cpu_cost=0.05, vram_mb=400.0),
            SettingOption("High", rt_cost=0.40, cpu_cost=0.09, vram_mb=700.0),
        ),
        default_option="Off / None",
        tex2_subsettings="Directional RT Shadows, Local RT Shadows, RT Shadow LOD",
        tooltip_en=(
            "Replaces shadow maps with ray-traced sun & local light shadows. "
            "Disabled on base consoles; stresses RT cores, BVH CPU traversal, and VRAM."
        ),
        tooltip_fa=(
            "سایه‌های خورشید و نورهای محلی با ردیابی پرتو. روی کنسول‌های پایه خاموش است؛ "
            "فشار همزمان بر RT، پردازنده (BVH) و VRAM دارد."
        ),
    ),
    SettingDefinition(
        id="reflections",
        name="Reflection Quality",
        category="Lighting & RT",
        badges=("RT", "GPU", "VRAM"),
        options=(
            SettingOption("Low", rt_cost=0.00, raster_cost=0.00, vram_mb=0.0),
            SettingOption("Medium", rt_cost=0.14, raster_cost=0.06, vram_mb=250.0),
            SettingOption("High", rt_cost=0.32, raster_cost=0.12, vram_mb=550.0),
        ),
        default_option="Low",
        tex2_subsettings="RT Reflections,SSR Hybrid Fallback, Roughness Cutoff, Car Paint Reflections",
        tooltip_en=(
            "Controls ray-traced reflection resolution and trace distance on wet Vice City streets "
            "and vehicle bodies. Low is the console baseline."
        ),
        tooltip_fa=(
            "دقت و برد بازتاب‌های ردیابی پرتو روی آسفالت خیس و بدنه خودروها. "
            "تنظیم Low مبنای کنسول‌های PS5 و Xbox است."
        ),
    ),
    SettingDefinition(
        id="bvh_quality",
        name="BVH Quality",
        category="Lighting & RT",
        badges=("CPU", "RT", "VRAM"),
        options=(
            SettingOption("Low", cpu_cost=-0.08, vram_mb=-350.0),
            SettingOption("Medium", cpu_cost=-0.04, vram_mb=-180.0),
            SettingOption("High", cpu_cost=0.00, rt_cost=0.00, vram_mb=0.0),
            SettingOption("Ultra", cpu_cost=0.13, rt_cost=0.05, vram_mb=450.0),
        ),
        default_option="High",
        tex2_subsettings="RT BVH Geometry LOD, Dynamic Instance Rebuild, Foliage BVH Inclusion",
        tooltip_en=(
            "Controls how much world geometry is updated in the ray-tracing acceleration structure "
            "each frame. Ultra hits CPU simulation threads and 1% lows hard during high-speed driving."
        ),
        tooltip_fa=(
            "حجم هندسه دنیای بازی در ساختار BVH برای ردیابی پرتو را تعیین می‌کند. "
            "حالت Ultra فشار زیادی به پردازنده و افت فریم‌های لحظه‌ای (1% Low) می‌آورد."
        ),
    ),
    SettingDefinition(
        id="raster_shadows",
        name="Directional & Local Raster Shadows",
        category="Lighting & RT",
        badges=("GPU", "VRAM"),
        options=(
            SettingOption("Low", raster_cost=-0.06),
            SettingOption("Medium", raster_cost=-0.03),
            SettingOption("High", raster_cost=0.00, vram_mb=0.0),
            SettingOption("Ultra", raster_cost=0.08, vram_mb=150.0),
        ),
        default_option="High",
        tex2_subsettings="Directional Shadow Cascades, Local Spot/Point Shadow Resolution, Softness",
        tooltip_en=(
            "Rasterized shadow map cascade resolution and local streetlamp/interior shadow pools."
        ),
        tooltip_fa=(
            "وضوح سایه‌های سنتی خورشید و منابع نوری شهری مثل چراغ‌های خیابان و خودروها."
        ),
    ),
    SettingDefinition(
        id="texture_quality",
        name="Texture Quality",
        category="Textures & World",
        badges=("VRAM", "GPU"),
        options=(
            SettingOption("Medium", vram_mb=-1300.0),
            SettingOption("High", vram_mb=0.0),
            SettingOption("Ultra", vram_mb=1600.0, raster_cost=0.02),
        ),
        default_option="High",
        tex2_subsettings="World Streaming Pool, Mip Bias, Anisotropic Quality, Normal/Roughness Maps",
        tooltip_en=(
            "Primary driver of VRAM allocation. Almost zero FPS penalty until VRAM overflows, "
            "at which point 8GB cards suffer severe PCIe stutter."
        ),
        tooltip_fa=(
            "مهم‌ترین عامل مصرف حافظه VRAM. تا زمانی که VRAM پر نشود افت فریم کمی دارد، "
            "اما روی کارت‌های ۸ گیگابایتی در حالت Ultra باعث لگ شدید می‌شود."
        ),
    ),
    SettingDefinition(
        id="vehicle_textures",
        name="Vehicle Max Texture & HD Count",
        category="Textures & World",
        badges=("VRAM",),
        options=(
            SettingOption("Medium", vram_mb=-500.0),
            SettingOption("High", vram_mb=-200.0),
            SettingOption("Ultra", vram_mb=0.0),
        ),
        default_option="Ultra",
        tex2_subsettings="Vehicle Max Texture Size, Simultaneous HD Vehicle Pool",
        tooltip_en=(
            "Limits how many nearby vehicles retain uncompressed HD liveries and interior textures "
            "simultaneously. Drop to High/Medium to save 200-500 MB VRAM on 8GB GPUs."
        ),
        tooltip_fa=(
            "تعداد خودروهای هم‌زمان با بافت HD را کنترل می‌کند. کاهش آن به High یا Medium "
            "حدود ۲۰۰ تا ۵۰۰ مگابایت VRAM ذخیره می‌کند."
        ),
    ),
    SettingDefinition(
        id="trees_terrain_grass",
        name="Trees / Terrain / Grass & Alpha Shadows",
        category="Textures & World",
        badges=("GPU", "CPU", "VRAM"),
        options=(
            SettingOption("Low", raster_cost=-0.07, cpu_cost=-0.03),
            SettingOption("Medium", raster_cost=0.00, cpu_cost=0.00, vram_mb=0.0),
            SettingOption("High", raster_cost=0.12, cpu_cost=0.04, vram_mb=250.0),
        ),
        default_option="Medium",
        tex2_subsettings="Tree Density & LOD, Terrain Detail, Grass Shadows, Foliage Alpha Shadows",
        tooltip_en=(
            "Foliage geometry, grass shadow casting, and Leonida wetlands alpha-tested shadows. "
            "High adds noticeable GPU raster & CPU draw-call overhead."
        ),
        tooltip_fa=(
            "جزئیات پوشش گیاهی، درختان نخل و سایه علفزارها. در حالت High هم بار GPU و هم "
            "تعداد فراخوانی‌های CPU را افزایش می‌دهد."
        ),
    ),
    SettingDefinition(
        id="lod_scale",
        name="LOD Scale",
        category="Textures & World",
        badges=("CPU", "GPU", "VRAM"),
        options=(
            SettingOption("0.8", cpu_cost=-0.06, raster_cost=-0.05),
            SettingOption("1.0", cpu_cost=0.00, raster_cost=0.00, vram_mb=0.0),
            SettingOption("1.2", cpu_cost=0.12, raster_cost=0.09, vram_mb=350.0),
        ),
        default_option="1.0",
        tex2_subsettings="World Geometry LOD Distance, Building Detail Pop-in Scale",
        tooltip_en=(
            "Pushes geometric detail distance further across Vice City skylines. "
            "1.2 increases CPU draw calls, GPU geometry throughput, and VRAM usage."
        ),
        tooltip_fa=(
            "فاصله لود شدن جزئیات ساختمان‌ها و محیط را افزایش می‌دهد. مقدار 1.2 فشار قابل توجهی "
            "به CPU، GPU و VRAM وارد می‌کند."
        ),
    ),
    SettingDefinition(
        id="water_tessellation",
        name="Water & Tessellation Quality",
        category="Water",
        badges=("GPU", "VRAM"),
        options=(
            SettingOption("Low", raster_cost=-0.04, cpu_cost=-0.01),
            SettingOption("Medium", raster_cost=-0.02),
            SettingOption("High", raster_cost=0.00, cpu_cost=0.00, vram_mb=0.0),
            SettingOption("Ultra", raster_cost=0.05, cpu_cost=0.01, vram_mb=150.0),
        ),
        default_option="High",
        tex2_subsettings="Ocean FFT Wave Simulation, Shoreline Foam, Adaptive Terrain Tessellation",
        tooltip_en=(
            "Controls Vice Beach ocean wave physics shaders and hardware tessellation displacement."
        ),
        tooltip_fa=(
            "کیفیت شبیه‌سازی امواج اقیانوس و تسلیشن سطح آب و زمین را تنظیم می‌کند."
        ),
    ),
    SettingDefinition(
        id="volumetrics",
        name="Volumetrics Lighting & Scattering",
        category="Volumetrics & Particles",
        badges=("GPU", "VRAM"),
        options=(
            SettingOption("Low", raster_cost=-0.09),
            SettingOption("Medium", raster_cost=0.00, vram_mb=0.0),
            SettingOption("High", raster_cost=0.16, vram_mb=200.0),
            SettingOption("Ultra", raster_cost=0.28, vram_mb=350.0),
        ),
        default_option="Medium",
        tex2_subsettings="Volumetric Fog Froxels, Cloud Shadows, Atmospheric Scattering, Particle Lit Fog",
        tooltip_en=(
            "Froxel-based volumetric fog, Vice City neon haze, and volumetric clouds. "
            "Very heavy GPU compute/pixel shader cost at High and Ultra."
        ),
        tooltip_fa=(
            "مه حجمی، نورپردازی نئونی در هوا و ابرهای سه‌بعدی. در سطوح High و Ultra "
            "از سنگین‌ترین تنظیمات روی پردازنده گرافیکی (GPU) است."
        ),
    ),
    SettingDefinition(
        id="hair_quality",
        name="Hair Quality & Simulation",
        category="Hair",
        badges=("GPU", "CPU", "VRAM"),
        options=(
            SettingOption("Low", raster_cost=-0.04, cpu_cost=-0.02),
            SettingOption("Medium", raster_cost=-0.02),
            SettingOption("High", raster_cost=0.00, cpu_cost=0.00, vram_mb=0.0),
            SettingOption("Ultra", raster_cost=0.05, cpu_cost=0.02, vram_mb=150.0),
        ),
        default_option="High",
        tex2_subsettings="Strand-Based Hair Rendering, Wind & Character Hair Physics",
        tooltip_en=(
            "Strand-based hair tessellation and physics simulation for Lucia, Jason, and nearby NPCs."
        ),
        tooltip_fa=(
            "رندر تار‌به‌تار و فیزیک مو برای شخصیت‌های اصلی و عابران نزدیک."
        ),
    ),
    SettingDefinition(
        id="ped_vehicle_density",
        name="Pedestrian & Vehicle Density",
        category="Population / AI / Physics",
        badges=("CPU", "RAM", "VRAM"),
        options=(
            SettingOption("Low", cpu_cost=-0.25, ram_mb=-600.0, vram_mb=-250.0),
            SettingOption("Medium", cpu_cost=-0.14, ram_mb=-300.0),
            SettingOption("High", cpu_cost=0.00, ram_mb=0.0, vram_mb=0.0),
            SettingOption("Ultra", cpu_cost=0.18, ram_mb=550.0, vram_mb=300.0),
        ),
        default_option="High",
        tex2_subsettings="Pedestrian Crowd Budget, Traffic Vehicle Budget, Distant Impostor Density",
        tooltip_en=(
            "Biggest CPU & System RAM knob in GTA VI. Lowering from High to Medium or Low "
            "immediately lifts CPU-bottlenecked 1% Lows in downtown Vice City."
        ),
        tooltip_fa=(
            "بزرگ‌ترین مصرف‌کننده CPU و رم سیستم در GTA VI. کاهش آن به Medium یا Low "
            "بلافاصله گلوگاه پردازنده و افت فریم شهر را برطرف می‌کند."
        ),
    ),
    SettingDefinition(
        id="ai_physics",
        name="AI Behavior / Motion / Physics Quality",
        category="Population / AI / Physics",
        badges=("CPU",),
        options=(
            SettingOption("Medium", cpu_cost=-0.12),
            SettingOption("High", cpu_cost=0.00),
            SettingOption("Ultra", cpu_cost=0.14),
        ),
        default_option="High",
        tex2_subsettings="AI Navigation & Reaction Tick, Ragdoll/Cloth Physics, Vehicle Suspension Solver",
        tooltip_en=(
            "Controls NPC crowd decision frequency, animation blending, and rigid-body physics ticks. "
            "Pure CPU simulation cost."
        ),
        tooltip_fa=(
            "دقت هوش مصنوعی، واکنش عابران، فیزیک تصادفات و انیمیشن‌ها را کنترل می‌کند؛ "
            "تأثیر مستقیم و خالص بر پردازنده (CPU) دارد."
        ),
    ),
)

SETTING_BY_ID: dict[str, SettingDefinition] = {s.id: s for s in SETTINGS}
RESOLUTION_BY_ID: dict[str, ResolutionProfile] = {r.id: r for r in RESOLUTIONS}
UPSCALER_BY_ID: dict[str, UpscalerProfile] = {u.id: u for u in UPSCALERS}
FRAME_GEN_BY_ID: dict[str, FrameGenProfile] = {f.id: f for f in FRAME_GEN_MODES}


def default_settings_map() -> dict[str, str]:
    """Return the PS5 / Series X baseline setting dictionary."""
    return {s.id: s.default_option for s in SETTINGS}


SETTINGS_PRESETS: tuple[SettingsPreset, ...] = (
    SettingsPreset(
        id="series_s",
        label="Series S",
        values={
            "rtgi": "Medium",
            "rt_shadows": "Off / None",
            "reflections": "Low",
            "bvh_quality": "Medium",
            "raster_shadows": "Medium",
            "texture_quality": "Medium",
            "vehicle_textures": "Medium",
            "trees_terrain_grass": "Low",
            "lod_scale": "0.8",
            "water_tessellation": "Medium",
            "volumetrics": "Low",
            "hair_quality": "Medium",
            "ped_vehicle_density": "Medium",
            "ai_physics": "Medium",
        },
        description_en="Xbox Series S parity profile: trimmed crowds, Medium textures, reduced LOD & volumetrics.",
        description_fa="پروفایل معادل Xbox Series S: جمعیت و بافت Medium و کاهش حجم دود و جزئیات دور.",
    ),
    SettingsPreset(
        id="ps5_xsx",
        label="PS5 / Series X",
        values=default_settings_map(),
        description_en="Leaked Tex2 PS5 / Series X baseline (RTGI Medium, RT Shadows Off, Reflections Low).",
        description_fa="پروفایل پایه PS5 / Series X مطابق جدول لورفته (RTGI Medium و بازتاب Low).",
    ),
    SettingsPreset(
        id="ps5_pro",
        label="PS5 Pro",
        values={
            "rtgi": "High",
            "rt_shadows": "Medium",
            "reflections": "Medium",
            "bvh_quality": "High",
            "raster_shadows": "High",
            "texture_quality": "High",
            "vehicle_textures": "Ultra",
            "trees_terrain_grass": "High",
            "lod_scale": "1.0",
            "water_tessellation": "High",
            "volumetrics": "High",
            "hair_quality": "High",
            "ped_vehicle_density": "High",
            "ai_physics": "High",
        },
        description_en="PS5 Pro enhanced RT profile: RTGI High, RT Shadows Medium, Reflections Medium.",
        description_fa="پروفایل ارتقایافته PS5 Pro با RTGI High، سایه RT متوسط و بازتاب Medium.",
    ),
    SettingsPreset(
        id="sweet_spot_900p",
        label="900p Sweet Spot",
        values={
            "rtgi": "Medium",
            "rt_shadows": "Medium",
            "reflections": "Low",
            "bvh_quality": "High",
            "raster_shadows": "High",
            "texture_quality": "High",
            "vehicle_textures": "High",
            "trees_terrain_grass": "Medium",
            "lod_scale": "1.0",
            "water_tessellation": "High",
            "volumetrics": "Medium",
            "hair_quality": "High",
            "ped_vehicle_density": "High",
            "ai_physics": "High",
        },
        resolution_id="900p",
        upscaler_id="native_aa",
        description_en="Crisp 900p Native AA sweet spot with RT Shadows On & BVH High for 12GB mid-range GPUs.",
        description_fa="پروفایل بهینه 900p Native AA همراه با سایه RT فعال و BVH High برای کارت‌های میان‌رده.",
    ),
    SettingsPreset(
        id="all_ultra",
        label="All Ultra",
        values={s.id: s.options[-1].label for s in SETTINGS},
        description_en="Maximum quality across every setting — extreme VRAM, RT, and CPU demand.",
        description_fa="حداکثر کیفیت در تمام گزینه‌ها؛ فشار بسیار سنگین بر VRAM، هسته‌های RT و CPU.",
    ),
)

SETTINGS_PRESET_BY_ID: dict[str, SettingsPreset] = {p.id: p for p in SETTINGS_PRESETS}
