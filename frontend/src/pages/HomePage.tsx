import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Container, Typography, Button, Box, Grid, CircularProgress, Switch, FormControlLabel } from '@mui/material';
import ShuffleIcon from '@mui/icons-material/Shuffle';
import { useSearchParams } from 'react-router-dom';
import { getImages, getRandomImages, ImageData } from '../api';
import ImageCard from '../components/ImageCard';

const HomePage: React.FC = () => {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [searchParams] = useSearchParams();
  const observerTarget = useRef<HTMLDivElement>(null);

  const fetchImages = async (pageNum: number, append: boolean = false) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    
    try {
      // URLパラメータを取得
      const personCountMin = searchParams.get('person_count_min');
      const personCountMax = searchParams.get('person_count_max');
      const exposureMin = searchParams.get('exposure_min');
      const exposureMax = searchParams.get('exposure_max');
      
      const response = await getImages(pageNum, {
        person_count_min: personCountMin,
        person_count_max: personCountMax,
        exposure_min: exposureMin,
        exposure_max: exposureMax,
      });
      
      if (append) {
        setImages(prev => [...prev, ...response.results]);
      } else {
        setImages(response.results);
      }
      
      // 次のページがあるかチェック
      setHasMore(response.next !== null);
    } catch (error) {
      console.error('Failed to fetch images:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const fetchRandomImages = async () => {
    setLoading(true);
    try {
      const randomImages = await getRandomImages();
      setImages(randomImages);
      setPage(1);
      setHasMore(false); // ランダム表示は無限スクロールしない
    } catch (error) {
      console.error('Failed to fetch random images:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初回読み込みとフィルタ変更時
  useEffect(() => {
    setPage(1);
    setHasMore(true);
    fetchImages(1, false);
  }, [searchParams]);

  // 無限スクロール用のIntersection Observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && !loadingMore) {
          const nextPage = page + 1;
          setPage(nextPage);
          fetchImages(nextPage, true);
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasMore, loading, loadingMore, page, searchParams]);

  return (
    <Container maxWidth={false} sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          地下アイドル画像ギャラリー
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={showInfo}
                onChange={(e) => setShowInfo(e.target.checked)}
              />
            }
            label="画像情報表示"
          />
          <Button
            variant="contained"
            startIcon={<ShuffleIcon />}
            onClick={fetchRandomImages}
          >
            ランダム表示
          </Button>
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Grid container spacing={1}>
            {images.map((image) => (
              <Grid item xs={12} sm={6} md={4} lg={3} xl={2} key={image.id}>
                <ImageCard image={image} showInfo={showInfo} />
              </Grid>
            ))}
          </Grid>
          
          {/* 無限スクロール用の監視ターゲット */}
          {hasMore && (
            <Box 
              ref={observerTarget}
              sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                py: 4,
                minHeight: '100px'
              }}
            >
              {loadingMore && <CircularProgress />}
            </Box>
          )}
        </>
      )}

      {!loading && images.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            画像がありません
          </Typography>
        </Box>
      )}
    </Container>
  );
};

export default HomePage;
