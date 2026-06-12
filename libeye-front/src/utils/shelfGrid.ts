import { SECTIONS } from '../constants/shelf';

// 💡 API locations 데이터를 '책장(Section-Shelf_num)' 기준으로 그룹화
export const groupLocations = (locations: any[]) => {
  const groups: Record<string, { section: string; shelf_num: number; levels: any[] }> = {};

  locations.forEach(loc => {
    const cleanSection = loc.section.replace('열', '').trim();
    const key = `${cleanSection}-${loc.shelf_num}`;

    if (!groups[key]) {
      groups[key] = { section: cleanSection, shelf_num: loc.shelf_num, levels: [] };
    }
    groups[key].levels.push(loc);
  });

  // 각 책장 내에서 단(level_num)을 1단~5단 순서로 정렬
  Object.values(groups).forEach(group => {
    group.levels.sort((a, b) => a.level_num - b.level_num);
  });

  return groups;
};

// 💡 새로운 엑셀 파일 기반 3층 그리드 레이아웃 생성 로직
export const buildGrid3F = (
  groupedLocations: Record<string, { section: string; shelf_num: number; levels: any[] }>
) => {
  const grid = [];
  const sections = SECTIONS;

  for (let r = 1; r <= 32; r++) {
    const row = [];
    for (let c = 0; c < 7; c++) {
      let hasShelf = false;

      if (c === 0) hasShelf = true; // A열 (1~32행)
      if (c === 1) hasShelf = true; // B열 (1~32행)
      if (c === 2 && r >= 5) hasShelf = true;  // C열 (5~32행)
      if (c === 3 && r >= 13) hasShelf = true; // D열 (13~32행)
      if (c === 4 && r >= 19) hasShelf = true; // E열 (19~32행)
      if (c === 5 && r >= 25) hasShelf = true; // F열 (25~32행)
      if (c === 6 && r >= 25) hasShelf = true; // G열 (25~32행)

      if (hasShelf) {
        const section = sections[c];
        const key = `${section}-${r}`;
        const groupData = groupedLocations[key] || { section, shelf_num: r, levels: [] };
        row.push(groupData);
      } else {
        row.push(null);
      }
    }
    grid.push(row);
  }
  return grid;
};
