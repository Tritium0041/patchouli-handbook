# Evidence: Billboards [Effects]

仅在 entry 无法覆盖细节、需要举例或冲突校验时再阅读此页。

## Metadata
- video_id: _o29OOOarPY
- published_at: unknown
- transcript_language: ja
- source_video_url: https://www.youtube.com/watch?v=_o29OOOarPY

## Summary
视频介绍了Billboard（公告板）技术在游戏特效中的应用。Billboard是始终面向摄像机的多边形，常用于粒子系统、爆炸效果及物品显示（如《超级马里奥64》中的铁球和炸弹王）。尽管现代游戏精细度提高，Billboard仍广泛存在，需注意Y轴Billboard等变体可能导致的视觉异常。

## Key Points
- Billboard是始终面向摄像机的多边形，通常为平面多边形。
- 在《超级马里奥64》中，滚落的铁球和炸弹王的眼睛、王冠使用了Billboard。
- 粒子系统（如爆炸火花）几乎都用Billboard渲染，因其成本低且适合无实体的效果。
- Y轴Billboard仅绕Y轴旋转面向相机，错误应用可能导致细长或扭曲的贴图。
- 现代游戏中Billboard难以察觉，但仍是特效的重要组成部分。

## Action Steps
1. 在设计粒子或特效时，优先考虑使用Billboard以降低渲染成本。
1. 注意区分全向Billboard和Y轴Billboard，避免错误应用于物体导致失真。
1. 测试不同摄像机角度下的Billboard表现，确保视觉效果合理。

## Notable Segments
- 00:03 | 定义Billboard是始终面向摄像机的多边形，通常是平面多边形。 | ビルボードというのはカメラに対して声帯するポリゴンのことです大抵の場合は板ポリゴンですが
- 00:14 | 举例《超级马里奥64》中滚落的铁球由Billboard构成。 | スーパーマリオ64の場合この坂から転げてくる鉄球はビルボードで構成されています
- 00:47 | 解释Billboard在特效中的重要性：几乎所有粒子（如爆炸）都使用Billboard渲染。 | なぜこの話がエフェクトに入っているのかというとパーティクルつまり粒子やその他のものは概ねビルボードで表示されることがほとんどだからです
- 01:30 | 警告Y轴Billboard仅绕Y轴旋转，错误使用会导致贴图变窄或扭曲。 | y軸ビルボードなどといいy軸の向きだけがカメラの方向に向くような設定が可能ですが間違えてエフェクトに適用すると細い絵が出てくるなんて場合があったりします