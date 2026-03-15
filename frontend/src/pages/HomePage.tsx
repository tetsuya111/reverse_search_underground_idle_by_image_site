import React, { useState, useEffect } from 'react';
import { Container, Typography, Button, Box, Grid, CircularProgress, Switch, FormControlLabel } from '@mui/material';
import ShuffleIcon from '@mui/icons-material/Shuffle';
import { getImages, getRandomImages, ImageData } from '../api';
import ImageCard from '../components/ImageCard';

const HomePage: React.FC = () => {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInfo, setShowInfo] = useState(false);
  const [page, setPage] = useState(1);

  const fetchImages = async () => {
    setLoading(true);
    try {
      const response = await getImages(page);
      setImages(response.results);
    } catch (error) {
      console.error('Failed to fetch images:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRandomImages = async () => {
    setLoading(true);
    try {
      const randomImages = await getRandomImages();
      setImages(randomImages);
    } catch (error) {
      console.error('Failed to fetch random images:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, [page]);

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
        <Grid container spacing={1}>
          {images.map((image) => (
            <Grid item xs={12} sm={6} md={4} lg={3} xl={2} key={image.id}>
              <ImageCard image={image} showInfo={showInfo} />
            </Grid>
          ))}
        </Grid>
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
