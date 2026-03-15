import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Chip, Grid, CircularProgress } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getTags, TagStat } from '../api';

const TagListPage: React.FC = () => {
  const [tags, setTags] = useState<TagStat[]>([]);
  const [loading, setLoading] = useState(true);

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
