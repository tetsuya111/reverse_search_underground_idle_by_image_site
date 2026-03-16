import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  CircularProgress,
  Link as MuiLink,
  Card,
  CardMedia,
} from '@mui/material';
import { getImageDetail, getSimilarImages, ImageData } from '../api';

const ImageDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [image, setImage] = useState<ImageData | null>(null);
  const [similarImages, setSimilarImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      
      setLoading(true);
      try {
        const imageData = await getImageDetail(parseInt(id));
        setImage(imageData);
        
        const similar = await getSimilarImages(parseInt(id));
        setSimilarImages(similar);
      } catch (error) {
        console.error('Failed to fetch image detail:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!image) {
    return (
      <Container>
        <Typography variant="h6">画像が見つかりません</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={4}>
        <Grid size={{xs:12,md:8}}>
          <Box sx={{ mb: 3 }}>
            <img
              src={image.image}
              alt={`Image ${image.id}`}
              style={{
                width: '100%',
                height: 'auto',
                maxHeight: '80vh',
                objectFit: 'contain',
              }}
            />
          </Box>
          <MuiLink href={image.source_url} target="_blank" rel="noopener noreferrer">
            取得元: {image.source_url}
          </MuiLink>
        </Grid>

        <Grid size={{xs:12,md:4}}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h5" gutterBottom>
              画像詳細
            </Typography>
            {image.idol_info && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" color="text.secondary">
                  グループ名
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  {image.idol_info.group_name || 'なし'}
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                  アイドル名
                </Typography>
                <Typography variant="body1">
                  {image.idol_info.idol_name || 'なし'}
                </Typography>
              </Box>
            )}
            <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 1 }}>
              タグ
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {image.tags.map((tag) => (
                <Chip key={tag.id} label={tag.tag_name} />
              ))}
            </Box>
          </Box>
        </Grid>
      </Grid>

      {similarImages.length > 0 && (
        <Box sx={{ mt: 6 }}>
          <Typography variant="h5" gutterBottom>
            同じタグの画像
          </Typography>
          <Grid container spacing={1}>
            {similarImages.map((similar) => (
              <Grid size={{xs:6,sm:4,md:3,lg:2}} key={similar.id}>
                <Card>
                  <MuiLink href={`/image/${similar.id}`}>
                    <CardMedia
                      component="img"
                      image={similar.image}
                      alt={`Similar ${similar.id}`}
                      sx={{ 
                        height: 150, 
                        objectFit: 'cover',
                        '&:hover': {
                          opacity: 0.8,
                        }
                      }}
                    />
                  </MuiLink>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Container>
  );
};

export default ImageDetailPage;
