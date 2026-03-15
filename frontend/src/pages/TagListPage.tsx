import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Chip, 
  Grid, 
  CircularProgress, 
  Slider,
  Paper,
  Button
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { getTags, TagStat } from '../api';

const TagListPage: React.FC = () => {
  const [tags, setTags] = useState<TagStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [personCountRange, setPersonCountRange] = useState<number[]>([1, 10]);
  const [exposureRange, setExposureRange] = useState<number[]>([0, 100]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTags = async () => {
      setLoading(true);
      try {
        const tagData = await getTags();
        setTags(tagData);
      } catch (error) {
        console.error('Failed to fetch tags:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTags();
  }, []);

  const handlePersonCountChange = (event: Event, newValue: number | number[]) => {
    setPersonCountRange(newValue as number[]);
  };

  const handleExposureChange = (event: Event, newValue: number | number[]) => {
    setExposureRange(newValue as number[]);
  };

  const handleApplyFilters = () => {
    const params = new URLSearchParams();
    params.set('person_count_min', personCountRange[0].toString());
    params.set('person_count_max', personCountRange[1].toString());
    params.set('exposure_min', exposureRange[0].toString());
    params.set('exposure_max', exposureRange[1].toString());
    navigate(`/?${params.toString()}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        タグ一覧
      </Typography>

      {/* フィルターセクション */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          画像フィルター
        </Typography>
        
        {/* 人数スライダー */}
        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>
            女の子の人数: {personCountRange[0]} 〜 {personCountRange[1]}人
          </Typography>
          <Slider
            value={personCountRange}
            onChange={handlePersonCountChange}
            valueLabelDisplay="auto"
            min={1}
            max={10}
            marks={[
              { value: 1, label: '1人' },
              { value: 5, label: '5人' },
              { value: 10, label: '10人' },
            ]}
          />
        </Box>

        {/* 露出度スライダー */}
        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>
            露出度: {exposureRange[0]} 〜 {exposureRange[1]}
          </Typography>
          <Slider
            value={exposureRange}
            onChange={handleExposureChange}
            valueLabelDisplay="auto"
            min={0}
            max={100}
            marks={[
              { value: 0, label: '0' },
              { value: 25, label: '25' },
              { value: 50, label: '50' },
              { value: 75, label: '75' },
              { value: 100, label: '100' },
            ]}
          />
        </Box>

        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleApplyFilters}
          fullWidth
        >
          フィルターを適用
        </Button>
      </Paper>

      {/* タグ一覧 */}
      <Typography variant="h6" gutterBottom>
        すべてのタグ
      </Typography>
      <Box sx={{ mt: 3 }}>
        <Grid container spacing={2}>
          {tags.map((tag, index) => (
            <Grid item key={index}>
              <Chip
                label={`${tag.tag_name} (${tag.count})`}
                component={RouterLink}
                to={`/?tag=${encodeURIComponent(tag.tag_name)}`}
                clickable
                sx={{ fontSize: '1rem', py: 2, px: 1 }}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
      {tags.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            タグがありません
          </Typography>
        </Box>
      )}
    </Container>
  );
};

export default TagListPage;
