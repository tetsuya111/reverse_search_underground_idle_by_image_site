import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ImageTag {
  id: number;
  tag_name: string;
}

export interface IdolInfo {
  id: number;
  group_name: string;
  idol_name: string;
}

export interface ImageData {
  id: number;
  image: string;
  source_url: string;
  tags: ImageTag[];
  idol_info?: IdolInfo;
  created_at: string;
}

export interface TagStat {
  tag_name: string;
  count: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ImageFilterParams {
  person_count_min?: string | null;
  person_count_max?: string | null;
  exposure_min?: string | null;
  exposure_max?: string | null;
}

// 画像一覧取得
export const getImages = async (
  page: number = 1,
  tag:string = "",
  filters?: ImageFilterParams
): Promise<PaginatedResponse<ImageData>> => {
  //let url = `/images/by_tag/?page=${page}`;
  let url = `/images/?page=${page}`;
  if(tag){
    url+=`&tag=${tag}`;
  }
  
  if (filters?.person_count_min) {
    url += `&person_count_min=${filters.person_count_min}`;
  }
  if (filters?.person_count_max) {
    url += `&person_count_max=${filters.person_count_max}`;
  }
  if (filters?.exposure_min) {
    url += `&exposure_min=${filters.exposure_min}`;
  }
  if (filters?.exposure_max) {
    url += `&exposure_max=${filters.exposure_max}`;
  }
  
  const response = await apiClient.get<PaginatedResponse<ImageData>>(url);
  return response.data;
};

// 画像詳細取得
export const getImageDetail = async (id: number): Promise<ImageData> => {
  const response = await apiClient.get<ImageData>(`/images/${id}/`);
  return response.data;
};

// ランダム画像取得
export const getRandomImages = async (): Promise<ImageData[]> => {
  const response = await apiClient.get<ImageData[]>('/images/random/');
  return response.data;
};

// 類似画像取得
export const getSimilarImages = async (id: number): Promise<ImageData[]> => {
  const response = await apiClient.get<ImageData[]>(`/images/${id}/similar/`);
  return response.data;
};

// タグで画像検索
export const getImagesByTag = async (tag: string, page: number = 1): Promise<PaginatedResponse<ImageData>> => {
  const response = await apiClient.get<PaginatedResponse<ImageData>>(`/images/by_tag/?tag=${encodeURIComponent(tag)}&page=${page}`);
  return response.data;
};

// タグ一覧取得
export const getTags = async (): Promise<TagStat[]> => {
  const response = await apiClient.get<TagStat[]>('/tags/');
  return response.data;
};

export default apiClient;
