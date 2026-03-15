import React from 'react';
import { Card, CardMedia, CardContent, Typography, Chip, Box, Link as MuiLink, IconButton, Collapse } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ImageData } from '../api';

interface ImageCardProps {
  image: ImageData;
  showInfo: boolean;
}

const ImageCard: React.FC<ImageCardProps> = ({ image, showInfo }) => {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <MuiLink href={image.source_url} target="_blank" rel="noopener noreferrer">
        <CardMedia
          component="img"
          image={image.image}
          alt={`Image ${image.id}`}
          sx={{ 
            height: 200, 
            objectFit: 'cover',
            '&:hover': {
              opacity: 0.8,
            }
          }}
        />
      </MuiLink>
      <Collapse in={showInfo}>
        <CardContent>
          {image.idol_info && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {image.idol_info.group_name && `${image.idol_info.group_name} - `}
                {image.idol_info.idol_name}
              </Typography>
            </Box>
          )}
          <Box sx={{ mb: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {image.tags.slice(0, 5).map((tag) => (
              <Chip key={tag.id} label={tag.tag_name} size="small" />
            ))}
            {image.tags.length > 5 && (
              <Chip label={`+${image.tags.length - 5}`} size="small" />
            )}
          </Box>
          <IconButton
            component={RouterLink}
            to={`/image/${image.id}`}
            size="small"
            sx={{ mt: 1 }}
          >
            <ExpandMoreIcon />
          </IconButton>
        </CardContent>
      </Collapse>
    </Card>
  );
};

export default ImageCard;
